"""Tests for the `secrets sync` CLI surface (VIBE-212: --app / --only for fly)."""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from vibe.cli.secrets import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestSyncAppAndOnlyValidation:
    """`--app`/`--only` are fly-specific and rejected for other providers."""

    def test_only_rejected_for_vercel(self, runner: CliRunner, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("A=1\n")

        result = runner.invoke(main, ["sync", str(env_file), "-p", "vercel", "--only", "A"])

        assert result.exit_code == 1
        assert "only supported for the fly provider" in result.output

    def test_app_rejected_for_github(self, runner: CliRunner, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("A=1\n")

        result = runner.invoke(main, ["sync", str(env_file), "-p", "github", "-a", "x"])

        assert result.exit_code == 1
        assert "only supported for the fly provider" in result.output


class TestSyncDryRun:
    """Dry-run shows key NAMES and the resolved app, never values."""

    def test_dry_run_shows_resolved_app_from_flag(self, runner: CliRunner, tmp_path: Path) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("LINEAR_API_KEY=secret-value\n")

        result = runner.invoke(
            main,
            ["sync", str(env_file), "-p", "fly", "-a", "vibe-claude-runner", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "vibe-claude-runner" in result.output
        assert "LINEAR_API_KEY" in result.output
        assert "secret-value" not in result.output

    def test_only_filters_displayed_keys_and_warns_on_missing(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("A=1\nB=2\nC=3\n")

        result = runner.invoke(
            main,
            ["sync", str(env_file), "-p", "fly", "-a", "app", "--only", "A,MISSING", "--dry-run"],
        )

        assert result.exit_code == 0
        assert "Found 1 secrets to sync" in result.output
        assert "  - A" in result.output
        assert "MISSING" in result.output  # warned as not found


class TestSyncFlyImport:
    """The fly sync path drives a single atomic `fly secrets import`."""

    def test_app_override_and_only_reach_fly_import(
        self, runner: CliRunner, tmp_path: Path
    ) -> None:
        env_file = tmp_path / ".env"
        env_file.write_text("LINEAR_API_KEY=lin\nSLACK_BOT_TOKEN=slack\nVERCEL_TOKEN=vt\n")

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            result = runner.invoke(
                main,
                [
                    "sync",
                    str(env_file),
                    "-p",
                    "fly",
                    "-a",
                    "vibe-claude-runner",
                    "--only",
                    "LINEAR_API_KEY,SLACK_BOT_TOKEN",
                ],
            )

        assert result.exit_code == 0
        import_calls = [
            c
            for c in mock_run.call_args_list
            if c.args and c.args[0][:3] == ["fly", "secrets", "import"]
        ]
        assert len(import_calls) == 1
        cmd = import_calls[0].args[0]
        assert cmd == ["fly", "secrets", "import", "-a", "vibe-claude-runner"]
        assert import_calls[0].kwargs["input"] == "LINEAR_API_KEY=lin\nSLACK_BOT_TOKEN=slack\n"
        assert "Synced 2/2" in result.output
