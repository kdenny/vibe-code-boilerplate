"""Tests for the PR auto-link feature in lib/vibe/cli/main.py."""

from unittest.mock import MagicMock, patch

from lib.vibe.cli.main import _autolink_pr_to_ticket


class TestAutolinkPrToTicket:
    """Tests for _autolink_pr_to_ticket helper function."""

    def test_autolink_linear_success(self) -> None:
        config = {"tracker": {"type": "linear", "config": {"team_id": "team_abc"}}}
        mock_tracker = MagicMock()

        with patch("lib.vibe.trackers.linear.LinearTracker", return_value=mock_tracker):
            _autolink_pr_to_ticket("PROJ-123", "https://github.com/org/repo/pull/42", config)

        mock_tracker.comment_ticket.assert_called_once_with(
            "PROJ-123",
            "PR opened: https://github.com/org/repo/pull/42",
        )

    def test_autolink_shortcut_success(self) -> None:
        config = {"tracker": {"type": "shortcut", "config": {}}}
        mock_tracker = MagicMock()

        with patch("lib.vibe.trackers.shortcut.ShortcutTracker", return_value=mock_tracker):
            _autolink_pr_to_ticket("SC-456", "https://github.com/org/repo/pull/43", config)

        mock_tracker.comment_ticket.assert_called_once_with(
            "SC-456",
            "PR opened: https://github.com/org/repo/pull/43",
        )

    def test_autolink_no_pr_url(self) -> None:
        config = {"tracker": {"type": "linear", "config": {}}}
        # Should return immediately without doing anything
        _autolink_pr_to_ticket("PROJ-123", "", config)
        # No assertion needed — just verifying it doesn't crash

    def test_autolink_no_ticket_in_branch(self) -> None:
        config = {"tracker": {"type": "linear", "config": {}}}
        # Branch name without a ticket pattern
        _autolink_pr_to_ticket("feature-branch", "https://github.com/org/repo/pull/44", config)
        # Should return without attempting to comment

    def test_autolink_no_tracker_configured(self) -> None:
        config = {"tracker": {"type": None, "config": {}}}
        _autolink_pr_to_ticket("PROJ-123", "https://github.com/org/repo/pull/45", config)
        # Should return without attempting to comment

    def test_autolink_tracker_error_is_caught(self) -> None:
        config = {"tracker": {"type": "linear", "config": {"team_id": "team_abc"}}}
        mock_tracker = MagicMock()
        mock_tracker.comment_ticket.side_effect = RuntimeError("API error")

        with patch("lib.vibe.trackers.linear.LinearTracker", return_value=mock_tracker):
            # Should not raise — error is caught and logged
            _autolink_pr_to_ticket("PROJ-123", "https://github.com/org/repo/pull/46", config)

    def test_autolink_extracts_ticket_from_complex_branch(self) -> None:
        config = {"tracker": {"type": "linear", "config": {"team_id": "team_abc"}}}
        mock_tracker = MagicMock()

        with patch("lib.vibe.trackers.linear.LinearTracker", return_value=mock_tracker):
            _autolink_pr_to_ticket(
                "feat/PROJ-789-add-feature",
                "https://github.com/org/repo/pull/47",
                config,
            )

        mock_tracker.comment_ticket.assert_called_once_with(
            "PROJ-789",
            "PR opened: https://github.com/org/repo/pull/47",
        )

    def test_autolink_empty_tracker_config(self) -> None:
        config: dict = {}
        _autolink_pr_to_ticket("PROJ-123", "https://github.com/org/repo/pull/48", config)
        # Should return without error when config has no tracker section
