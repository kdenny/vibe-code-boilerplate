"""Unit tests for the `vibe-run-event` CLI (bin/vibe-run-event)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from vibe.cli.run_event import main


@pytest.fixture
def runner_in_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    # default_telemetry() resolves .vibe/telemetry under CWD; isolate it.
    monkeypatch.chdir(tmp_path)
    # No Linear creds -> LogSink only, fully hermetic.
    monkeypatch.delenv("LINEAR_API_KEY", raising=False)
    return CliRunner()


def _start(runner: CliRunner, *args: str):
    return runner.invoke(main, ["start", "--ticket", "VIBE-146", *args])


class TestStart:
    def test_prints_run_id(self, runner_in_tmp: CliRunner) -> None:
        result = _start(runner_in_tmp)
        assert result.exit_code == 0
        assert result.output.strip()  # the run id

    def test_json_includes_running_state(self, runner_in_tmp: CliRunner) -> None:
        result = _start(runner_in_tmp, "--json")
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["state"] == "running"
        assert data["ticket"] == "VIBE-146"


class TestCompleteRoundTrip:
    def test_start_then_complete_via_current_run(self, runner_in_tmp: CliRunner) -> None:
        assert _start(runner_in_tmp).exit_code == 0
        result = runner_in_tmp.invoke(main, ["complete", "--outcome", "success"])
        assert result.exit_code == 0
        assert "success" in result.output

    def test_complete_rejects_bad_outcome(self, runner_in_tmp: CliRunner) -> None:
        _start(runner_in_tmp)
        result = runner_in_tmp.invoke(main, ["complete", "--outcome", "merged"])
        assert result.exit_code != 0  # not one of success|failure|timeout

    def test_complete_without_run_errors_cleanly(self, runner_in_tmp: CliRunner) -> None:
        result = runner_in_tmp.invoke(main, ["complete", "--outcome", "failure"])
        assert result.exit_code != 0
        assert "current run" in result.output.lower()


class TestListAndReconcile:
    def test_list_shows_started_run(self, runner_in_tmp: CliRunner) -> None:
        start = _start(runner_in_tmp, "--json")
        run_id = json.loads(start.output)["run_id"]
        result = runner_in_tmp.invoke(main, ["list"])
        assert run_id in result.output

    def test_reconcile_no_stale_runs(self, runner_in_tmp: CliRunner) -> None:
        result = runner_in_tmp.invoke(main, ["reconcile"])
        assert result.exit_code == 0
        assert "No stale runs" in result.output

    def test_reconcile_json_empty_list(self, runner_in_tmp: CliRunner) -> None:
        result = runner_in_tmp.invoke(main, ["reconcile", "--json"])
        assert json.loads(result.output) == []
