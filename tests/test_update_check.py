"""Tests for automatic boilerplate update checking."""

from datetime import datetime, timedelta
from unittest.mock import patch

from lib.vibe.update_check import (
    _compare_versions,
    _should_check,
    check_for_update,
    format_update_notice,
    skip_update_check,
)


class TestCompareVersions:
    def test_remote_newer_patch(self):
        assert _compare_versions("1.0.0", "1.0.1") is True

    def test_remote_newer_minor(self):
        assert _compare_versions("1.0.0", "1.1.0") is True

    def test_remote_newer_major(self):
        assert _compare_versions("1.0.0", "2.0.0") is True

    def test_same_version(self):
        assert _compare_versions("1.0.0", "1.0.0") is False

    def test_local_newer(self):
        assert _compare_versions("1.1.0", "1.0.0") is False

    def test_invalid_local(self):
        assert _compare_versions("invalid", "1.0.0") is False

    def test_invalid_remote(self):
        assert _compare_versions("1.0.0", "invalid") is False

    def test_empty_string(self):
        assert _compare_versions("", "1.0.0") is False


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

    @patch("lib.vibe.update_check.load_state")
    @patch("lib.vibe.update_check.save_state")
    @patch("lib.vibe.update_check._fetch_upstream_version")
    @patch("lib.vibe.update_check.get_version", return_value="1.0.0")
    @patch("lib.vibe.update_check.load_config", return_value={})
    def test_update_available(self, mock_config, mock_ver, mock_fetch, mock_save, mock_load):
        mock_load.return_value = {}
        mock_fetch.return_value = "1.1.0"
        result = check_for_update(force=True)
        assert result is not None
        assert result["current_version"] == "1.0.0"
        assert result["upstream_version"] == "1.1.0"

    @patch("lib.vibe.update_check.load_state")
    @patch("lib.vibe.update_check.save_state")
    @patch("lib.vibe.update_check._fetch_upstream_version")
    @patch("lib.vibe.update_check.get_version", return_value="1.0.0")
    @patch("lib.vibe.update_check.load_config", return_value={})
    def test_already_up_to_date(self, mock_config, mock_ver, mock_fetch, mock_save, mock_load):
        mock_load.return_value = {}
        mock_fetch.return_value = "1.0.0"
        result = check_for_update(force=True)
        assert result is None

    @patch("lib.vibe.update_check.load_state")
    @patch("lib.vibe.update_check.save_state")
    @patch("lib.vibe.update_check._fetch_upstream_version")
    @patch("lib.vibe.update_check.get_version", return_value="1.0.0")
    @patch("lib.vibe.update_check.load_config", return_value={})
    def test_network_failure_returns_none(
        self, mock_config, mock_ver, mock_fetch, mock_save, mock_load
    ):
        mock_load.return_value = {}
        mock_fetch.return_value = None
        result = check_for_update(force=True)
        assert result is None

    @patch("lib.vibe.update_check.load_state")
    @patch("lib.vibe.update_check.save_state")
    def test_cached_update_returned_within_interval(self, mock_save, mock_load):
        recent = (datetime.now() - timedelta(hours=1)).isoformat()
        mock_load.return_value = {
            "boilerplate_last_check": recent,
            "boilerplate_upstream_version": "2.0.0",
        }
        with patch("lib.vibe.update_check.get_version", return_value="1.0.0"):
            result = check_for_update()
        assert result is not None
        assert result["cached"] is True
        assert result["upstream_version"] == "2.0.0"

    @patch("lib.vibe.update_check.load_state")
    @patch("lib.vibe.update_check.save_state")
    def test_no_cached_update_when_versions_match(self, mock_save, mock_load):
        recent = (datetime.now() - timedelta(hours=1)).isoformat()
        mock_load.return_value = {
            "boilerplate_last_check": recent,
            "boilerplate_upstream_version": "1.0.0",
        }
        with patch("lib.vibe.update_check.get_version", return_value="1.0.0"):
            result = check_for_update()
        assert result is None

    @patch("lib.vibe.update_check.load_state")
    @patch("lib.vibe.update_check.save_state")
    @patch("lib.vibe.update_check._fetch_upstream_version")
    @patch("lib.vibe.update_check.get_version", return_value="1.0.0")
    @patch("lib.vibe.update_check.load_config", return_value={})
    def test_saves_state_after_check(self, mock_config, mock_ver, mock_fetch, mock_save, mock_load):
        mock_load.return_value = {}
        mock_fetch.return_value = "1.1.0"
        check_for_update(force=True)
        mock_save.assert_called_once()
        saved_state = mock_save.call_args[0][0]
        assert "boilerplate_last_check" in saved_state
        assert saved_state["boilerplate_upstream_version"] == "1.1.0"
        assert saved_state["boilerplate_current_version"] == "1.0.0"

    @patch("lib.vibe.update_check.load_state")
    @patch("lib.vibe.update_check.save_state")
    @patch("lib.vibe.update_check._fetch_upstream_version")
    @patch("lib.vibe.update_check.get_version", return_value="1.0.0")
    def test_uses_custom_upstream_repo(self, mock_ver, mock_fetch, mock_save, mock_load):
        mock_load.return_value = {}
        mock_fetch.return_value = "1.0.0"
        with patch(
            "lib.vibe.update_check.load_config",
            return_value={"boilerplate": {"source_repo": "custom/repo"}},
        ):
            check_for_update(force=True)
        mock_fetch.assert_called_once_with("custom/repo")


class TestSkipUpdateCheck:
    @patch("lib.vibe.update_check.load_state")
    @patch("lib.vibe.update_check.save_state")
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
