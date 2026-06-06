"""Seam: PR Autopilot setup preflight + vibe.ui validation.

Run the real :func:`setup_pr_autopilot` flow — real :func:`configure_pr_autopilot`,
real TOML artifact IO on a temp filesystem, and the real ``SetupValidator`` from
``vibe.ui`` — with only the subprocess boundary faked via an injected provider
runner. Network is never touched (Linear/Axiom env vars are unset), so the Linear
check exercises its real offline branch. Proves the integration composes the
centralized validator and gates enablement end-to-end.
"""

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
from vibe.integrations.pr_autopilot.setup import setup_pr_autopilot

ProviderRunner = Callable[[Sequence[str]], ToolResult]


def _runner(*, secret_present: bool) -> ProviderRunner:
    secrets_payload = json.dumps(
        [{"name": "ANTHROPIC_API_KEY"}] if secret_present else [{"name": "OTHER"}]
    )

    def run(command: Sequence[str]) -> ToolResult:
        cmd = tuple(command)
        if cmd[:3] == ("gh", "repo", "view"):
            return ToolResult(cmd, 0, json.dumps({"owner": {"login": "acme"}, "name": "widgets"}))
        if cmd[:3] == ("gh", "secret", "list"):
            return ToolResult(cmd, 0, secrets_payload)
        if cmd[:3] == ("gh", "auth", "status"):
            return ToolResult(cmd, 0, "")
        return ToolResult(cmd, 1, "", "no origin")

    return run


@pytest.fixture(autouse=True)
def _offline_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("LINEAR_API_KEY", "AXIOM_TOKEN", "LINEAR_TEAM"):
        monkeypatch.delenv(var, raising=False)


def _make_workflow_assets(base: Path) -> None:
    for rel in (".claude/commands/pr-autopilot.md", "recipes/workflows/pr-autopilot.md"):
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("loop\n")


def test_ready_setup_writes_enabled_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _make_workflow_assets(tmp_path)

    text = setup_pr_autopilot(runner=_runner(secret_present=True))

    # Composed the real ui.validation Linear check (offline -> soft warning).
    assert "linear logging" in text
    assert "Result: READY" in text

    # Real artifacts on disk, enabled.
    assert INTEGRATION_CONFIG_PATH.exists()
    assert not DISABLED_CONFIG_PATH.exists()
    artifact = INTEGRATION_CONFIG_PATH.read_text()
    assert "enabled = true" in artifact
    assert 'owner = "acme"' in (tmp_path / ".vibe" / "config.toml").read_text()


def test_failed_preflight_leaves_integration_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    _make_workflow_assets(tmp_path)

    text = setup_pr_autopilot(runner=_runner(secret_present=False))

    assert "Result: NOT READY" in text
    # Gate held: configure ran, but the failed preflight disabled the integration.
    assert not INTEGRATION_CONFIG_PATH.exists()
    assert DISABLED_CONFIG_PATH.exists()
    # Inferred artifacts are preserved for the re-run after remediation.
    assert 'owner = "acme"' in (tmp_path / ".vibe" / "config.toml").read_text()
