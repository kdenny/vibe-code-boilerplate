"""Tests for automatic boilerplate update checking."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from vibe.update_check import (
    _compare_versions,
    _should_check,
    check_for_update,
    format_update_notice,
    skip_update_check,
)


@pytest.fixture(autouse=True)
def _enable_update_check(monkeypatch: pytest.MonkeyPatch) -> None:
    """Re-enable the update check for this module.

    The global ``_hermetic_env`` fixture sets ``VIBE_NO_UPDATE_CHECK=1`` so CLI
    tests don't emit the update banner. These tests exercise the update-check
    logic directly, so they must run with the short-circuit disabled.
    """
    monkeypatch.delenv("VIBE_NO_UPDATE_CHECK", raising=False)


class TestCompareVersions:
    @pytest.mark.parametrize(
        ("local", "remote", "expected"),
        [
            ("1.0.0", "1.0.1", True),  # remote newer (patch)
            ("1.0.0", "1.1.0", True),  # remote newer (minor)
            ("1.0.0", "2.0.0", True),  # remote newer (major)
            ("1.0.0", "1.0.0", False),  # same version
            ("1.1.0", "1.0.0", False),  # local newer
            ("invalid", "1.0.0", False),  # invalid local
            ("1.0.0", "invalid", False),  # invalid remote
            ("", "1.0.0", False),  # empty local
        ],
    )
    def test_compare_versions(self, local: str, remote: str, expected: bool) -> None:
        assert _compare_versions(local, remote) is expected


class TestShouldCheck:
    def test_no_last_check(self):
        assert _should_check({}) is True

    def test_none_last_check(self):
        assert _should_check({"boilerplate_last_check": None}) is True

    def test_recent_check(self):
        recent = (datetime.now() - timedelta(hours=1)).isoformat()
        assert _should_check({"boilerplate_last_check": recent}) is False

    def test_old_check(self):
        old = (datetime.now() - timedelta(days=8)).isoformat()
        assert _should_check({"boilerplate_last_check": old}) is True

    def test_exactly_7_days(self):
        boundary = (datetime.now() - timedelta(days=7, seconds=1)).isoformat()
        assert _should_check({"boilerplate_last_check": boundary}) is True

    def test_invalid_timestamp(self):
        assert _should_check({"boilerplate_last_check": "not-a-date"}) is True


class TestCheckForUpdate:
    @patch.dict("os.environ", {"VIBE_NO_UPDATE_CHECK": "1"})
    def test_disabled_via_env(self):
        assert check_for_update() is None

    @patch("vibe.update_check.load_state")
    @patch("vibe.update_check.save_state")
    @patch("vibe.update_check._fetch_upstream_version")
    @patch("vibe.update_check.get_version", return_value="1.0.0")
    @patch("vibe.update_check.load_config", return_value={})
    def test_update_available(self, mock_config, mock_ver, mock_fetch, mock_save, mock_load):
        mock_load.return_value = {}
        mock_fetch.return_value = "1.1.0"
        result = check_for_update(force=True)
        assert result is not None
        assert result["current_version"] == "1.0.0"
        assert result["upstream_version"] == "1.1.0"

    @patch("vibe.update_check.load_state")
    @patch("vibe.update_check.save_state")
    @patch("vibe.update_check._fetch_upstream_version")
    @patch("vibe.update_check.get_version", return_value="1.0.0")
    @patch("vibe.update_check.load_config", return_value={})
    def test_already_up_to_date(self, mock_config, mock_ver, mock_fetch, mock_save, mock_load):
        mock_load.return_value = {}
        mock_fetch.return_value = "1.0.0"
        result = check_for_update(force=True)
        assert result is None

    @patch("vibe.update_check.load_state")
    @patch("vibe.update_check.save_state")
    @patch("vibe.update_check._fetch_upstream_version")
    @patch("vibe.update_check.get_version", return_value="1.0.0")
    @patch("vibe.update_check.load_config", return_value={})
    def test_network_failure_returns_none(
        self, mock_config, mock_ver, mock_fetch, mock_save, mock_load
    ):
        mock_load.return_value = {}
        mock_fetch.return_value = None
        result = check_for_update(force=True)
        assert result is None

    @patch("vibe.update_check.load_state")
    @patch("vibe.update_check.save_state")
    def test_cached_update_returned_within_interval(self, mock_save, mock_load):
        recent = (datetime.now() - timedelta(hours=1)).isoformat()
        mock_load.return_value = {
            "boilerplate_last_check": recent,
            "boilerplate_upstream_version": "2.0.0",
        }
        with patch("vibe.update_check.get_version", return_value="1.0.0"):
            result = check_for_update()
        assert result is not None
        assert result["cached"] is True
        assert result["upstream_version"] == "2.0.0"

    @patch("vibe.update_check.load_state")
    @patch("vibe.update_check.save_state")
    def test_no_cached_update_when_versions_match(self, mock_save, mock_load):
        recent = (datetime.now() - timedelta(hours=1)).isoformat()
        mock_load.return_value = {
            "boilerplate_last_check": recent,
            "boilerplate_upstream_version": "1.0.0",
        }
        with patch("vibe.update_check.get_version", return_value="1.0.0"):
            result = check_for_update()
        assert result is None

    @patch("vibe.update_check.load_state")
    @patch("vibe.update_check.save_state")
    @patch("vibe.update_check._fetch_upstream_version")
    @patch("vibe.update_check.get_version", return_value="1.0.0")
    @patch("vibe.update_check.load_config", return_value={})
    def test_saves_state_after_check(self, mock_config, mock_ver, mock_fetch, mock_save, mock_load):
        mock_load.return_value = {}
        mock_fetch.return_value = "1.1.0"
        check_for_update(force=True)
        mock_save.assert_called_once()
        saved_state = mock_save.call_args[0][0]
        assert "boilerplate_last_check" in saved_state
        assert saved_state["boilerplate_upstream_version"] == "1.1.0"
        assert saved_state["boilerplate_current_version"] == "1.0.0"

    @patch("vibe.update_check.load_state")
    @patch("vibe.update_check.save_state")
    @patch("vibe.update_check._fetch_upstream_version")
    @patch("vibe.update_check.get_version", return_value="1.0.0")
    def test_uses_custom_upstream_repo(self, mock_ver, mock_fetch, mock_save, mock_load):
        mock_load.return_value = {}
        mock_fetch.return_value = "1.0.0"
        with patch(
            "vibe.update_check.load_config",
            return_value={"boilerplate": {"source_repo": "custom/repo"}},
        ):
            check_for_update(force=True)
        mock_fetch.assert_called_once_with("custom/repo")


class TestSkipUpdateCheck:
    @patch("vibe.update_check.load_state")
    @patch("vibe.update_check.save_state")
    def test_resets_timer_and_clears_upstream(self, mock_save, mock_load):
        mock_load.return_value = {
            "boilerplate_last_check": "2020-01-01T00:00:00",
            "boilerplate_upstream_version": "2.0.0",
        }
        skip_update_check()
        saved_state = mock_save.call_args[0][0]
        assert "boilerplate_upstream_version" not in saved_state
        # Last check should be recent
        last_check = datetime.fromisoformat(saved_state["boilerplate_last_check"])
        assert datetime.now() - last_check < timedelta(seconds=5)


class TestFormatUpdateNotice:
    def test_includes_versions(self):
        notice = format_update_notice(
            {
                "current_version": "1.0.0",
                "upstream_version": "1.2.0",
            }
        )
        assert "1.0.0" in notice
        assert "1.2.0" in notice
        assert "bin/vibe update" in notice

    def test_includes_skip_instruction(self):
        notice = format_update_notice(
            {
                "current_version": "1.0.0",
                "upstream_version": "2.0.0",
            }
        )
        assert "--skip" in notice


class TestUpdateNoticeGating:
    """The update notice is interactive-only: it must never leak into pipes,
    CI, or --json output. The CLI group callback gates it on stderr being a TTY.
    """

    UPDATE = {"current_version": "1.0.0", "upstream_version": "2.0.0", "cached": True}

    def test_notice_suppressed_when_stderr_not_a_tty(self) -> None:
        from vibe.cli import main as main_mod

        fake_sys = MagicMock()
        fake_sys.stderr.isatty.return_value = False
        with (
            patch.object(main_mod, "sys", fake_sys),
            patch("vibe.update_check.check_for_update", return_value=self.UPDATE) as mock_check,
            patch("vibe.cli.main.click.echo") as mock_echo,
        ):
            main_mod.main.callback()

        # Non-interactive: don't even hit the network, and never echo the notice.
        mock_check.assert_not_called()
        mock_echo.assert_not_called()

    def test_notice_shown_when_stderr_is_a_tty(self) -> None:
        from vibe.cli import main as main_mod

        fake_sys = MagicMock()
        fake_sys.stderr.isatty.return_value = True
        with (
            patch.object(main_mod, "sys", fake_sys),
            patch("vibe.update_check.check_for_update", return_value=self.UPDATE),
            patch("vibe.cli.main.click.echo") as mock_echo,
        ):
            main_mod.main.callback()

        mock_echo.assert_called_once()
        # Notice goes to stderr.
        assert mock_echo.call_args.kwargs.get("err") is True

    def test_json_output_is_clean_when_update_available(self) -> None:
        """Reproduces the original failure: an available update must not pollute
        --json output captured by CliRunner (which mixes stderr into output)."""
        import json

        from click.testing import CliRunner

        from vibe.cli import main as main_mod

        mock_tracker = MagicMock()
        mock_tracker.list_labels.return_value = [{"name": "Bug", "id": "1"}]
        fake_sys = MagicMock()
        fake_sys.stderr.isatty.return_value = True

        runner = CliRunner()
        with (
            patch.object(main_mod, "sys", fake_sys),
            patch("vibe.update_check.check_for_update", return_value=self.UPDATE) as mock_check,
            patch(
                "vibe.config.load_config",
                return_value={
                    "tracker": {"type": "linear", "config": {"team_id": "t1"}},
                    "labels": {},
                },
            ),
            patch("vibe.trackers.linear.LinearTracker", return_value=mock_tracker),
            patch(
                "vibe.label_sync.load_config",
                return_value={"tracker": {"type": "linear", "config": {}}, "labels": {}},
            ),
            patch("vibe.label_sync.save_config"),
            patch.dict("os.environ", {"LINEAR_API_KEY": "test-key"}),
        ):
            result = runner.invoke(main_mod.main, ["sync-labels", "--json"])

        assert result.exit_code == 0
        mock_check.assert_not_called()
        # Must parse cleanly even though an update is "available".
        payload = json.loads(result.output)
        assert "labels" in payload
        assert "Boilerplate update available" not in result.output
