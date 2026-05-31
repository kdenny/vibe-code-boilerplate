"""Seam: preflight detects missing workflow assets, remediation closes the loop.

Runs the real :func:`run_preflight` and :func:`remediate_pr_autopilot` together
against a real filesystem, mocking only the true boundary (the git/gh runner).
The point of the seam is that the asset the preflight flags as *missing* is
exactly the asset remediation *creates* — so a second preflight no longer flags
it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from vibe.integrations.pr_autopilot.prototype import ToolResult
from vibe.integrations.pr_autopilot.remediation import remediate_pr_autopilot
from vibe.integrations.pr_autopilot.setup import WORKFLOW_ASSETS, run_preflight


def _runner(command: tuple[str, ...]) -> ToolResult:
    # Auth/secret probes the preflight makes; git/gh actions the remediation makes.
    if command[:3] == ("gh", "pr", "create"):
        return ToolResult(command=command, returncode=0, stdout="https://x/pull/1")
    return ToolResult(command=command, returncode=0)


def _workflow_assets_check(runner):
    report = run_preflight(runner=runner)
    return next(c for c in report.checks if c.result.name == "workflow assets")


def test_remediation_resolves_the_preflight_workflow_asset_gap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)

    # Before: the loop assets are absent, so the preflight flags them.
    before = _workflow_assets_check(_runner)
    assert not before.result.success
    for asset in WORKFLOW_ASSETS:
        assert str(asset) in before.result.message

    # Remediate (opt-in confirmed) — writes the missing assets and "opens" a PR.
    out = remediate_pr_autopilot(confirm=lambda _preview: True, runner=_runner)
    assert "Opened remediation PR" in out

    # After: the same preflight check now passes against the real files written.
    for asset in WORKFLOW_ASSETS:
        assert (tmp_path / asset).exists()
    after = _workflow_assets_check(_runner)
    assert after.result.success
