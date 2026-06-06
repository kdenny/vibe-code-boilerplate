"""Unit tests for PR Autopilot config remediation (VIBE-145)."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibe.integrations.pr_autopilot.prototype import ToolResult
from vibe.integrations.pr_autopilot.remediation import (
    REMEDIABLE_ASSETS,
    REMEDIATION_BRANCH,
    RemediableAsset,
    detect_remediation_plan,
    remediate_pr_autopilot,
)
from vibe.integrations.pr_autopilot.setup import WORKFLOW_ASSETS


def _fake_runner(*, fail_on: tuple[str, ...] | None = None, pr_url: str = "https://x/pull/1"):
    calls: list[tuple[str, ...]] = []

    def run(command: tuple[str, ...]) -> ToolResult:
        calls.append(command)
        if fail_on is not None and command[: len(fail_on)] == fail_on:
            return ToolResult(command=command, returncode=1, stderr="boom")
        stdout = pr_url if command[:3] == ("gh", "pr", "create") else ""
        return ToolResult(command=command, returncode=0, stdout=stdout)

    run.calls = calls  # type: ignore[attr-defined]
    return run


def _write_all_assets(root: Path) -> None:
    for asset in REMEDIABLE_ASSETS:
        target = root / asset.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("present\n", encoding="utf-8")


# --- detection -------------------------------------------------------------


def test_detect_finds_every_missing_asset(tmp_path: Path) -> None:
    plan = detect_remediation_plan(root=tmp_path)
    assert not plan.empty
    assert set(plan.paths) == {str(asset.path) for asset in REMEDIABLE_ASSETS}


def test_detect_skips_present_assets(tmp_path: Path) -> None:
    _write_all_assets(tmp_path)
    plan = detect_remediation_plan(root=tmp_path)
    assert plan.empty
    assert plan.paths == ()


def test_detect_reports_only_the_missing_one(tmp_path: Path) -> None:
    _write_all_assets(tmp_path)
    missing = REMEDIABLE_ASSETS[0]
    (tmp_path / missing.path).unlink()

    plan = detect_remediation_plan(root=tmp_path)

    assert plan.paths == (str(missing.path),)
    assert plan.items[0].content  # template content was loaded


# --- bundled templates -----------------------------------------------------


@pytest.mark.parametrize("asset", REMEDIABLE_ASSETS, ids=lambda a: str(a.path))
def test_every_asset_has_nonempty_bundled_template(asset: RemediableAsset) -> None:
    assert asset.render().strip()


def test_loop_assets_cover_preflight_workflow_assets() -> None:
    # Remediation must be able to fix every loop asset the preflight detects.
    remediable = {asset.path for asset in REMEDIABLE_ASSETS}
    assert set(WORKFLOW_ASSETS).issubset(remediable)


# --- guided flow -----------------------------------------------------------


def test_nothing_to_remediate_when_all_present(tmp_path: Path) -> None:
    _write_all_assets(tmp_path)
    out = remediate_pr_autopilot(root=tmp_path, runner=_fake_runner())
    assert "nothing to remediate" in out


def test_dry_run_reports_plan_without_touching_git(tmp_path: Path) -> None:
    runner = _fake_runner()
    out = remediate_pr_autopilot(root=tmp_path, runner=runner, dry_run=True)

    assert "Dry run" in out
    assert ".coderabbit.yaml" in out
    assert runner.calls == []  # type: ignore[attr-defined]
    # No files written on a dry run.
    assert not (tmp_path / ".coderabbit.yaml").exists()


def test_declined_opens_no_pr(tmp_path: Path) -> None:
    runner = _fake_runner()
    out = remediate_pr_autopilot(root=tmp_path, runner=runner, confirm=lambda _preview: False)

    assert "Declined" in out
    assert runner.calls == []  # type: ignore[attr-defined]
    assert not (tmp_path / ".github/PULL_REQUEST_TEMPLATE.md").exists()


def test_confirmed_writes_assets_and_opens_pr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = _fake_runner(pr_url="https://github.com/acme/app/pull/7")

    out = remediate_pr_autopilot(confirm=lambda _preview: True, runner=runner)

    # Every missing asset was written from its bundled template.
    for asset in REMEDIABLE_ASSETS:
        assert (tmp_path / asset.path).read_text(encoding="utf-8") == asset.render()

    commands = [cmd[:3] for cmd in runner.calls]  # type: ignore[attr-defined]
    assert commands[0] == ("git", "checkout", "-b")
    assert ("git", "add", str(REMEDIABLE_ASSETS[0].path)) == runner.calls[1][:3]  # type: ignore[attr-defined]
    assert any(cmd[:3] == ("git", "commit", "-m") for cmd in runner.calls)  # type: ignore[attr-defined]
    assert any(cmd[:3] == ("git", "push", "-u") for cmd in runner.calls)  # type: ignore[attr-defined]
    assert any(cmd[:3] == ("gh", "pr", "create") for cmd in runner.calls)  # type: ignore[attr-defined]
    assert "https://github.com/acme/app/pull/7" in out


def test_pr_targets_base_branch_with_policy_aligned_body(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = _fake_runner()

    remediate_pr_autopilot(confirm=lambda _preview: True, runner=runner)

    pr_create = next(
        cmd
        for cmd in runner.calls
        if cmd[:3] == ("gh", "pr", "create")  # type: ignore[attr-defined]
    )
    assert "--base" in pr_create and pr_create[pr_create.index("--base") + 1] == "main"
    assert "--head" in pr_create and pr_create[pr_create.index("--head") + 1] == REMEDIATION_BRANCH
    body = pr_create[pr_create.index("--body") + 1]
    # Body follows PULL_REQUEST_TEMPLATE.md headings + a Low Risk assessment.
    assert "## Summary" in body and "## Risk Assessment" in body
    assert "Low Risk" in body


def test_base_branch_read_from_integration_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config = tmp_path / ".vibe/pr-autopilot.toml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text('[automation]\nbase_branch = "trunk"\n', encoding="utf-8")
    runner = _fake_runner()

    remediate_pr_autopilot(confirm=lambda _preview: True, runner=runner)

    pr_create = next(
        cmd
        for cmd in runner.calls
        if cmd[:3] == ("gh", "pr", "create")  # type: ignore[attr-defined]
    )
    assert pr_create[pr_create.index("--base") + 1] == "trunk"


def test_failed_checkout_leaves_working_tree_clean(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = _fake_runner(fail_on=("git", "checkout"))

    out = remediate_pr_autopilot(confirm=lambda _preview: True, runner=runner)

    assert "Remediation stopped" in out
    # Branch creation failed first, so no asset files were written.
    assert not (tmp_path / ".coderabbit.yaml").exists()
    # And no commit/push/PR was attempted.
    assert all(cmd[:1] != ("gh",) for cmd in runner.calls)  # type: ignore[attr-defined]
