"""Tests for the guided PR Autopilot setup preflight."""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest

from vibe.integrations.pr_autopilot.prototype import (
    DISABLED_CONFIG_PATH,
    INTEGRATION_CONFIG_PATH,
    ToolResult,
)
from vibe.integrations.pr_autopilot.setup import (
    PreflightCheck,
    PreflightReport,
    _check_anthropic_secret,
    _check_axiom_optional,
    _check_core_config,
    _check_linear_logging,
    _check_workflow_assets,
    run_preflight,
    setup_pr_autopilot,
)
from vibe.ui.validation import ValidationResult

ProviderRunner = Callable[[Sequence[str]], ToolResult]


def _runner(
    *,
    repo_ok: bool = True,
    auth_ok: bool = True,
    secret_present: bool = True,
    secret_list_ok: bool = True,
) -> ProviderRunner:
    """Fake provider runner dispatching by command at the subprocess boundary."""

    secrets_payload = json.dumps(
        [{"name": "ANTHROPIC_API_KEY"}] if secret_present else [{"name": "OTHER"}]
    )

    def run(command: Sequence[str]) -> ToolResult:
        cmd = tuple(command)
        if cmd[:3] == ("gh", "repo", "view"):
            if repo_ok:
                return ToolResult(
                    cmd, 0, json.dumps({"owner": {"login": "acme"}, "name": "widgets"})
                )
            return ToolResult(cmd, 1, "", "not found")
        if cmd[:3] == ("gh", "secret", "list"):
            if secret_list_ok:
                return ToolResult(cmd, 0, secrets_payload)
            return ToolResult(cmd, 1, "", "no auth")
        if cmd[:3] == ("gh", "auth", "status"):
            return ToolResult(cmd, 0 if auth_ok else 1, "", "" if auth_ok else "not logged in")
        if cmd[:2] == ("git", "remote"):
            return ToolResult(cmd, 1, "", "no origin")
        return ToolResult(cmd, 0, "", "")

    return run


def _make_workflow_assets(base: Path) -> None:
    for rel in (".claude/commands/pr-autopilot.md", "recipes/workflows/pr-autopilot.md"):
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("loop\n")


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("LINEAR_API_KEY", "AXIOM_TOKEN", "LINEAR_TEAM"):
        monkeypatch.delenv(var, raising=False)


def test_setup_ready_enables(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    _make_workflow_assets(tmp_path)

    text = setup_pr_autopilot(runner=_runner(secret_present=True, auth_ok=True))

    assert "Result: READY" in text
    assert "PR Autopilot enabled" in text
    assert INTEGRATION_CONFIG_PATH.exists()
    assert not DISABLED_CONFIG_PATH.exists()
    # Soft checks warn but never block enablement.
    assert "WARN linear logging" in text
    assert "WARN axiom (optional)" in text


def test_setup_not_ready_when_secret_missing_disables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _make_workflow_assets(tmp_path)

    text = setup_pr_autopilot(runner=_runner(secret_present=False))

    assert "Result: NOT READY" in text
    assert "1 required check failed" in text
    assert "gh secret set ANTHROPIC_API_KEY" in text
    assert not INTEGRATION_CONFIG_PATH.exists()
    assert DISABLED_CONFIG_PATH.exists()


def test_setup_not_ready_when_workflow_assets_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)  # no workflow assets created

    text = setup_pr_autopilot(runner=_runner(secret_present=True, auth_ok=True))

    assert "Result: NOT READY" in text
    assert "FAIL workflow assets" in text
    assert "Restore the PR-autopilot loop assets" in text
    assert not INTEGRATION_CONFIG_PATH.exists()


def test_run_preflight_reports_inferred_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _make_workflow_assets(tmp_path)
    # Configure first so the preflight has artifacts to read.
    setup_pr_autopilot(runner=_runner(secret_present=False))

    report = run_preflight(runner=_runner(secret_present=False))

    assert report.inferred_github == "acme/widgets"
    assert not report.ready
    assert {check.result.name for check in report.checks} == {
        "core config",
        "integration config",
        "workflow assets",
        "github auth",
        "anthropic secret",
        "linear logging",
        "axiom (optional)",
    }


def test_check_core_config() -> None:
    ok = _check_core_config({"github": {"owner": "a", "repo": "b"}})
    assert ok.result.success and ok.required

    bad = _check_core_config({"github": {}})
    assert not bad.result.success and bad.blocking
    assert "configure" in (bad.result.details or "")


def test_check_anthropic_secret_three_states() -> None:
    present = _check_anthropic_secret(
        ToolResult(("gh",), 0, json.dumps([{"name": "ANTHROPIC_API_KEY"}]))
    )
    assert present.result.success and present.required

    absent = _check_anthropic_secret(ToolResult(("gh",), 0, json.dumps([{"name": "OTHER"}])))
    assert absent.blocking
    assert "gh secret set" in (absent.result.details or "")

    unknown = _check_anthropic_secret(ToolResult(("gh",), 1, "", "no auth"))
    assert unknown.blocking
    assert "could not read" in unknown.result.message


def test_check_workflow_assets_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    check = _check_workflow_assets()
    assert not check.result.success and check.blocking
    assert "pr-autopilot.md" in (check.result.message or "")


def test_soft_checks_are_non_blocking(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    monkeypatch.delenv("AXIOM_TOKEN", raising=False)

    linear = _check_linear_logging()
    axiom = _check_axiom_optional()

    assert not linear.required and not linear.blocking
    assert "LINEAR_API_KEY" in (linear.result.details or "")
    assert not axiom.required and not axiom.blocking

    monkeypatch.setenv("AXIOM_TOKEN", "tok")
    assert _check_axiom_optional().result.success


def test_preflight_check_labels() -> None:
    assert PreflightCheck(ValidationResult("x", True, "")).label == "PASS"
    assert PreflightCheck(ValidationResult("x", False, "")).label == "FAIL"
    assert PreflightCheck(ValidationResult("x", False, ""), required=False).label == "WARN"


def test_report_ready_when_only_soft_failures() -> None:
    report = PreflightReport(
        inferred_github="a/b",
        inferred_linear_team="unset",
        checks=(
            PreflightCheck(ValidationResult("hard", True, "ok")),
            PreflightCheck(ValidationResult("soft", False, "missing", "do x"), required=False),
        ),
    )
    assert report.ready
    assert report.warnings and not report.blocking_failures
