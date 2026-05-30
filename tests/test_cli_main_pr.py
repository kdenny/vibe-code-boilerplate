"""Tests for the PR auto-link feature in vibe/cli/main.py."""

from unittest.mock import MagicMock, patch

from vibe.cli.main import _autolink_pr_to_ticket, _mark_ticket_in_progress


class TestAutolinkPrToTicket:
    """Tests for _autolink_pr_to_ticket helper function."""

    def test_autolink_linear_success(self) -> None:
        config = {"tracker": {"type": "linear", "config": {"team_id": "team_abc"}}}
        mock_tracker = MagicMock()

        with patch("vibe.trackers.linear.LinearTracker", return_value=mock_tracker):
            _autolink_pr_to_ticket("PROJ-123", "https://github.com/org/repo/pull/42", config)

        mock_tracker.comment_ticket.assert_called_once_with(
            "PROJ-123",
            "PR opened: https://github.com/org/repo/pull/42",
        )

    def test_autolink_shortcut_success(self) -> None:
        config = {"tracker": {"type": "shortcut", "config": {}}}
        mock_tracker = MagicMock()

        with patch("vibe.trackers.shortcut.ShortcutTracker", return_value=mock_tracker):
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

        with patch("vibe.trackers.linear.LinearTracker", return_value=mock_tracker):
            # Should not raise — error is caught and logged
            _autolink_pr_to_ticket("PROJ-123", "https://github.com/org/repo/pull/46", config)

    def test_autolink_extracts_ticket_from_complex_branch(self) -> None:
        config = {"tracker": {"type": "linear", "config": {"team_id": "team_abc"}}}
        mock_tracker = MagicMock()

        with patch("vibe.trackers.linear.LinearTracker", return_value=mock_tracker):
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


class TestMarkTicketInProgress:
    """Tests for the _mark_ticket_in_progress helper used by `do`."""

    def test_marks_linear_ticket_in_progress(self) -> None:
        config = {"tracker": {"type": "linear", "config": {"team_id": "team_abc"}}}
        mock_tracker = MagicMock()
        mock_tracker.start_ticket.return_value = "In Progress"

        with patch("vibe.trackers.linear.LinearTracker", return_value=mock_tracker):
            _mark_ticket_in_progress("PROJ-123", config)

        mock_tracker.start_ticket.assert_called_once_with("PROJ-123")

    def test_skips_non_linear_tracker(self) -> None:
        config = {"tracker": {"type": "github", "config": {}}}
        # No LinearTracker should be constructed; just verify no crash.
        with patch("vibe.trackers.linear.LinearTracker") as mock_cls:
            _mark_ticket_in_progress("PROJ-123", config)
        mock_cls.assert_not_called()

    def test_skips_when_no_tracker_configured(self) -> None:
        config: dict = {"tracker": {"type": None, "config": {}}}
        _mark_ticket_in_progress("PROJ-123", config)
        # Should return without attempting anything

    def test_empty_config_is_safe(self) -> None:
        _mark_ticket_in_progress("PROJ-123", {})
        # Should not raise when config has no tracker section

    def test_tracker_error_is_swallowed(self) -> None:
        config = {"tracker": {"type": "linear", "config": {"team_id": "team_abc"}}}
        mock_tracker = MagicMock()
        mock_tracker.start_ticket.side_effect = RuntimeError("API error")

        with patch("vibe.trackers.linear.LinearTracker", return_value=mock_tracker):
            # Best-effort — must not raise so worktree creation continues.
            _mark_ticket_in_progress("PROJ-123", config)
