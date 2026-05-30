"""Tests for duplicate PR prevention in bin/vibe pr (#209).

Covers:
- _extract_ticket_id
- _check_existing_prs_for_ticket
- _check_local_state_for_ticket_conflicts
- _warn_duplicate_prs
- record_ticket_branch / get_ticket_branch / get_branches_for_ticket (state)
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from lib.vibe.cli.main import (
    _branch_record_is_stale,
    _check_existing_prs_for_ticket,
    _check_local_state_for_ticket_conflicts,
    _extract_ticket_id,
    _warn_duplicate_prs,
)
from lib.vibe.state import (
    get_branches_for_ticket,
    get_ticket_branch,
    record_ticket_branch,
)

# ---------------------------------------------------------------------------
# _extract_ticket_id
# ---------------------------------------------------------------------------


class TestExtractTicketId:
    def test_standard_branch(self) -> None:
        assert _extract_ticket_id("PROJ-123") == "PROJ-123"

    def test_branch_with_description(self) -> None:
        assert _extract_ticket_id("PROJ-456-add-login-page") == "PROJ-456"

    def test_prefixed_branch(self) -> None:
        assert _extract_ticket_id("feat/PROJ-789-stuff") == "PROJ-789"

    def test_no_ticket_id(self) -> None:
        assert _extract_ticket_id("feature-branch") is None

    def test_worktree_agent_branch(self) -> None:
        assert _extract_ticket_id("worktree-agent-abc123") is None

    def test_lowercase_no_match(self) -> None:
        assert _extract_ticket_id("proj-123") is None


# ---------------------------------------------------------------------------
# _check_existing_prs_for_ticket
# ---------------------------------------------------------------------------


class TestCheckExistingPrsForTicket:
    def test_finds_matching_prs(self) -> None:
        prs_json = json.dumps(
            [
                {
                    "number": 10,
                    "title": "PROJ-123: Add feature",
                    "state": "OPEN",
                    "url": "https://github.com/org/repo/pull/10",
                },
                {
                    "number": 5,
                    "title": "PROJ-123: First attempt",
                    "state": "MERGED",
                    "url": "https://github.com/org/repo/pull/5",
                },
            ]
        )
        mock_result = MagicMock(returncode=0, stdout=prs_json)
        with patch("lib.vibe.cli.main._subprocess.run", return_value=mock_result):
            result = _check_existing_prs_for_ticket("PROJ-123")
        assert len(result) == 2

    def test_filters_non_matching_titles(self) -> None:
        """PRs returned by search that don't contain the ticket ID in title are filtered out."""
        prs_json = json.dumps(
            [
                {"number": 10, "title": "PROJ-123: Add feature", "state": "OPEN", "url": "u1"},
                {
                    "number": 11,
                    "title": "Unrelated PR mentioning something else",
                    "state": "OPEN",
                    "url": "u2",
                },
            ]
        )
        mock_result = MagicMock(returncode=0, stdout=prs_json)
        with patch("lib.vibe.cli.main._subprocess.run", return_value=mock_result):
            result = _check_existing_prs_for_ticket("PROJ-123")
        assert len(result) == 1
        assert result[0]["number"] == 10

    def test_exact_match_does_not_flag_longer_ids(self) -> None:
        """PROJ-1 must not match PROJ-12 / PROJ-100 (gh --search is substring)."""
        prs_json = json.dumps(
            [
                {"number": 1, "title": "PROJ-1: The real one", "state": "OPEN", "url": "u1"},
                {"number": 12, "title": "PROJ-12: Different ticket", "state": "OPEN", "url": "u2"},
                {"number": 100, "title": "PROJ-100: Another one", "state": "MERGED", "url": "u3"},
                {"number": 13, "title": "Fixes PROJ-1 finally", "state": "OPEN", "url": "u4"},
            ]
        )
        mock_result = MagicMock(returncode=0, stdout=prs_json)
        with patch("lib.vibe.cli.main._subprocess.run", return_value=mock_result):
            result = _check_existing_prs_for_ticket("PROJ-1")
        # Only the two titles with PROJ-1 on a word boundary should match.
        assert sorted(r["number"] for r in result) == [1, 13]

    def test_match_is_case_insensitive(self) -> None:
        prs_json = json.dumps(
            [{"number": 7, "title": "proj-7: lowercase title", "state": "OPEN", "url": "u1"}]
        )
        mock_result = MagicMock(returncode=0, stdout=prs_json)
        with patch("lib.vibe.cli.main._subprocess.run", return_value=mock_result):
            result = _check_existing_prs_for_ticket("PROJ-7")
        assert len(result) == 1

    def test_empty_result(self) -> None:
        mock_result = MagicMock(returncode=0, stdout="[]")
        with patch("lib.vibe.cli.main._subprocess.run", return_value=mock_result):
            result = _check_existing_prs_for_ticket("PROJ-999")
        assert result == []

    def test_gh_not_found(self) -> None:
        with patch("lib.vibe.cli.main._subprocess.run", side_effect=FileNotFoundError):
            result = _check_existing_prs_for_ticket("PROJ-123")
        assert result == []

    def test_gh_timeout(self) -> None:
        with patch(
            "lib.vibe.cli.main._subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="gh", timeout=15),
        ):
            result = _check_existing_prs_for_ticket("PROJ-123")
        assert result == []

    def test_gh_nonzero_exit(self) -> None:
        mock_result = MagicMock(returncode=1, stdout="")
        with patch("lib.vibe.cli.main._subprocess.run", return_value=mock_result):
            result = _check_existing_prs_for_ticket("PROJ-123")
        assert result == []

    def test_malformed_json(self) -> None:
        mock_result = MagicMock(returncode=0, stdout="not json")
        with patch("lib.vibe.cli.main._subprocess.run", return_value=mock_result):
            result = _check_existing_prs_for_ticket("PROJ-123")
        assert result == []


# ---------------------------------------------------------------------------
# _check_local_state_for_ticket_conflicts
# ---------------------------------------------------------------------------


class TestCheckLocalStateForTicketConflicts:
    def test_no_conflicts(self) -> None:
        with patch(
            "lib.vibe.state.get_branches_for_ticket",
            return_value=[{"ticket_id": "PROJ-123", "branch": "PROJ-123"}],
        ):
            result = _check_local_state_for_ticket_conflicts("PROJ-123", "PROJ-123")
        assert result == []

    def test_detects_conflict(self) -> None:
        with patch(
            "lib.vibe.state.get_branches_for_ticket",
            return_value=[
                {
                    "ticket_id": "PROJ-123",
                    "branch": "PROJ-123-add-feature",
                    "worktree_path": "/some/path",
                }
            ],
        ):
            result = _check_local_state_for_ticket_conflicts("PROJ-123", "worktree-agent-abc")
        assert len(result) == 1
        assert result[0]["branch"] == "PROJ-123-add-feature"

    def test_no_entries(self) -> None:
        with patch("lib.vibe.state.get_branches_for_ticket", return_value=[]):
            result = _check_local_state_for_ticket_conflicts("PROJ-123", "PROJ-123")
        assert result == []

    def test_ignores_stale_branch_record(self) -> None:
        """A branch recorded long ago is treated as abandoned, not a conflict."""
        old = (datetime.now() - timedelta(days=90)).isoformat()
        with patch(
            "lib.vibe.state.get_branches_for_ticket",
            return_value=[
                {"ticket_id": "PROJ-123", "branch": "PROJ-123-old", "created_at": old},
            ],
        ):
            result = _check_local_state_for_ticket_conflicts("PROJ-123", "worktree-agent-abc")
        assert result == []

    def test_keeps_recent_branch_record(self) -> None:
        recent = (datetime.now() - timedelta(days=2)).isoformat()
        with patch(
            "lib.vibe.state.get_branches_for_ticket",
            return_value=[
                {"ticket_id": "PROJ-123", "branch": "PROJ-123-recent", "created_at": recent},
            ],
        ):
            result = _check_local_state_for_ticket_conflicts("PROJ-123", "worktree-agent-abc")
        assert len(result) == 1


class TestBranchRecordIsStale:
    def test_old_record_is_stale(self) -> None:
        old = (datetime.now() - timedelta(days=31)).isoformat()
        assert _branch_record_is_stale({"created_at": old}) is True

    def test_recent_record_is_not_stale(self) -> None:
        recent = (datetime.now() - timedelta(days=5)).isoformat()
        assert _branch_record_is_stale({"created_at": recent}) is False

    def test_missing_created_at_is_not_stale(self) -> None:
        # Fail safe: without a timestamp we keep the record (over-warn).
        assert _branch_record_is_stale({"branch": "PROJ-123-x"}) is False

    def test_unparseable_created_at_is_not_stale(self) -> None:
        assert _branch_record_is_stale({"created_at": "not-a-date"}) is False

    def test_tz_aware_created_at_is_not_stale(self) -> None:
        # An offset-aware created_at can't be subtracted from the offset-naive
        # datetime.now() — that raises TypeError. Fail safe (keep) rather than
        # blow up bin/vibe pr.
        assert _branch_record_is_stale({"created_at": "2026-01-01T00:00:00+00:00"}) is False

    def test_now_override_is_respected(self) -> None:
        created = "2026-01-01T00:00:00"
        # 10 days later -> not stale; 40 days later -> stale.
        assert _branch_record_is_stale({"created_at": created}, now=datetime(2026, 1, 11)) is False
        assert _branch_record_is_stale({"created_at": created}, now=datetime(2026, 2, 10)) is True


# ---------------------------------------------------------------------------
# _warn_duplicate_prs
# ---------------------------------------------------------------------------


class TestWarnDuplicatePrs:
    def test_no_duplicates_returns_true(self) -> None:
        with (
            patch("lib.vibe.cli.main._check_existing_prs_for_ticket", return_value=[]),
            patch("lib.vibe.cli.main._check_local_state_for_ticket_conflicts", return_value=[]),
        ):
            assert _warn_duplicate_prs("PROJ-123", "PROJ-123") is True

    def test_merged_pr_user_confirms(self) -> None:
        merged_pr = [
            {"number": 5, "title": "PROJ-123: Old PR", "state": "MERGED", "url": "u1"},
        ]
        with (
            patch("lib.vibe.cli.main._check_existing_prs_for_ticket", return_value=merged_pr),
            patch("lib.vibe.cli.main._check_local_state_for_ticket_conflicts", return_value=[]),
            patch("lib.vibe.cli.main.click.confirm", return_value=True),
            patch("lib.vibe.cli.main.click.echo"),
        ):
            assert _warn_duplicate_prs("PROJ-123", "PROJ-123") is True

    def test_merged_pr_user_aborts(self) -> None:
        merged_pr = [
            {"number": 5, "title": "PROJ-123: Old PR", "state": "MERGED", "url": "u1"},
        ]
        with (
            patch("lib.vibe.cli.main._check_existing_prs_for_ticket", return_value=merged_pr),
            patch("lib.vibe.cli.main._check_local_state_for_ticket_conflicts", return_value=[]),
            patch("lib.vibe.cli.main.click.confirm", return_value=False),
            patch("lib.vibe.cli.main.click.echo"),
        ):
            assert _warn_duplicate_prs("PROJ-123", "PROJ-123") is False

    def test_open_pr_user_confirms(self) -> None:
        open_pr = [
            {"number": 10, "title": "PROJ-123: In progress", "state": "OPEN", "url": "u1"},
        ]
        with (
            patch("lib.vibe.cli.main._check_existing_prs_for_ticket", return_value=open_pr),
            patch("lib.vibe.cli.main._check_local_state_for_ticket_conflicts", return_value=[]),
            patch("lib.vibe.cli.main.click.confirm", return_value=True),
            patch("lib.vibe.cli.main.click.echo"),
        ):
            assert _warn_duplicate_prs("PROJ-123", "PROJ-123") is True

    def test_local_conflict_user_aborts(self) -> None:
        conflict = [{"ticket_id": "PROJ-123", "branch": "PROJ-123-other", "worktree_path": "/p"}]
        with (
            patch("lib.vibe.cli.main._check_existing_prs_for_ticket", return_value=[]),
            patch(
                "lib.vibe.cli.main._check_local_state_for_ticket_conflicts",
                return_value=conflict,
            ),
            patch("lib.vibe.cli.main.click.confirm", return_value=False),
            patch("lib.vibe.cli.main.click.echo"),
        ):
            assert _warn_duplicate_prs("PROJ-123", "PROJ-123-new") is False

    def test_skip_confirmation_flag(self) -> None:
        merged_pr = [
            {"number": 5, "title": "PROJ-123: Old PR", "state": "MERGED", "url": "u1"},
        ]
        with (
            patch("lib.vibe.cli.main._check_existing_prs_for_ticket", return_value=merged_pr),
            patch("lib.vibe.cli.main._check_local_state_for_ticket_conflicts", return_value=[]),
            patch("lib.vibe.cli.main.click.echo"),
        ):
            # skip_confirmation=True means we always proceed
            assert _warn_duplicate_prs("PROJ-123", "PROJ-123", skip_confirmation=True) is True


# ---------------------------------------------------------------------------
# State: record_ticket_branch / get_ticket_branch / get_branches_for_ticket
# ---------------------------------------------------------------------------


class TestTicketBranchState:
    def test_record_and_retrieve(self, tmp_path: Path) -> None:
        record_ticket_branch(
            "PROJ-100", "PROJ-100-feature", worktree_path="/wt/100", base_path=tmp_path
        )
        result = get_ticket_branch("PROJ-100", base_path=tmp_path)
        assert result is not None
        assert result["branch"] == "PROJ-100-feature"
        assert result["worktree_path"] == "/wt/100"

    def test_no_entry_returns_none(self, tmp_path: Path) -> None:
        assert get_ticket_branch("PROJ-999", base_path=tmp_path) is None

    def test_get_branches_for_ticket(self, tmp_path: Path) -> None:
        record_ticket_branch("PROJ-200", "PROJ-200-a", base_path=tmp_path)
        branches = get_branches_for_ticket("PROJ-200", base_path=tmp_path)
        assert len(branches) == 1
        assert branches[0]["branch"] == "PROJ-200-a"

    def test_get_branches_for_ticket_no_match(self, tmp_path: Path) -> None:
        record_ticket_branch("PROJ-300", "PROJ-300-a", base_path=tmp_path)
        branches = get_branches_for_ticket("PROJ-301", base_path=tmp_path)
        assert branches == []

    def test_append_preserves_all_entries(self, tmp_path: Path) -> None:
        """Recording the same ticket twice appends; both branches are preserved."""
        record_ticket_branch("PROJ-400", "PROJ-400-first", base_path=tmp_path)
        record_ticket_branch("PROJ-400", "PROJ-400-second", base_path=tmp_path)

        # get_ticket_branch returns the most recent entry
        result = get_ticket_branch("PROJ-400", base_path=tmp_path)
        assert result is not None
        assert result["branch"] == "PROJ-400-second"

        # get_branches_for_ticket returns ALL entries
        branches = get_branches_for_ticket("PROJ-400", base_path=tmp_path)
        assert len(branches) == 2
        assert branches[0]["branch"] == "PROJ-400-first"
        assert branches[1]["branch"] == "PROJ-400-second"

    def test_backward_compat_old_dict_format(self, tmp_path: Path) -> None:
        """Old state files with a single dict per ticket are handled gracefully."""
        import json

        # Simulate old format: ticket_branches values are plain dicts, not lists
        state_file = tmp_path / ".vibe" / "local_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        old_state = {
            "ticket_branches": {
                "PROJ-500": {
                    "branch": "PROJ-500-legacy",
                    "worktree_path": "/old/path",
                    "created_at": "2025-01-01T00:00:00",
                }
            }
        }
        state_file.write_text(json.dumps(old_state))

        # get_ticket_branch should return the dict directly
        result = get_ticket_branch("PROJ-500", base_path=tmp_path)
        assert result is not None
        assert result["branch"] == "PROJ-500-legacy"

        # get_branches_for_ticket should wrap it in a list
        branches = get_branches_for_ticket("PROJ-500", base_path=tmp_path)
        assert len(branches) == 1
        assert branches[0]["branch"] == "PROJ-500-legacy"
