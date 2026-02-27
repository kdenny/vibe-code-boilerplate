"""Tests for GitHub Issues tracker integration."""

import json
from unittest.mock import MagicMock, patch

import pytest

from lib.vibe.trackers.github_issues import GitHubIssuesTracker, _gh


class TestGhHelper:
    """Tests for the _gh helper function."""

    def test_gh_success(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "output"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            result = _gh(["issue", "list"])

        assert result.stdout == "output"

    def test_gh_failure_raises(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "not found"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="gh issue list"):
                _gh(["issue", "list"])

    def test_gh_no_check(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "not found"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            result = _gh(["issue", "list"], check=False)

        assert result.returncode == 1


class TestGitHubIssuesTrackerInit:
    """Tests for GitHubIssuesTracker initialization."""

    def test_init_with_repo(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        assert tracker._repo == "owner/repo"

    def test_init_from_env(self) -> None:
        with patch.dict("os.environ", {"GITHUB_REPOSITORY": "env-owner/env-repo"}):
            tracker = GitHubIssuesTracker()
        assert tracker._repo == "env-owner/env-repo"

    def test_init_no_repo(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            tracker = GitHubIssuesTracker()
        assert tracker._repo is None


class TestGitHubIssuesTrackerName:
    """Tests for name property."""

    def test_name_returns_github(self) -> None:
        tracker = GitHubIssuesTracker()
        assert tracker.name == "github"


class TestGitHubIssuesTrackerAuthenticate:
    """Tests for authenticate method."""

    def test_authenticate_success(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            assert tracker.authenticate() is True

    def test_authenticate_failure(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "not logged in"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            assert tracker.authenticate() is False


class TestGitHubIssuesTrackerGetTicket:
    """Tests for get_ticket method."""

    def test_get_ticket_success(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        issue_data = {
            "number": 42,
            "title": "Fix the bug",
            "body": "Something is broken",
            "state": "OPEN",
            "labels": [{"name": "Bug"}, {"name": "High Risk"}],
            "url": "https://github.com/owner/repo/issues/42",
            "assignees": [{"login": "dev1"}],
            "milestone": None,
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(issue_data)

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            ticket = tracker.get_ticket("42")

        assert ticket is not None
        assert ticket.id == "#42"
        assert ticket.title == "Fix the bug"
        assert ticket.description == "Something is broken"
        assert ticket.status == "Open"
        assert ticket.labels == ["Bug", "High Risk"]
        assert ticket.assignee == "dev1"

    def test_get_ticket_with_hash_prefix(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        issue_data = {
            "number": 99,
            "title": "Test",
            "body": "",
            "state": "OPEN",
            "labels": [],
            "url": "https://github.com/owner/repo/issues/99",
            "assignees": [],
            "milestone": None,
        }

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(issue_data)

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result
        ) as mock_run:
            ticket = tracker.get_ticket("#99")

        assert ticket is not None
        assert ticket.id == "#99"
        # Verify the # was stripped in the gh command
        call_args = mock_run.call_args[0][0]
        assert "99" in call_args

    def test_get_ticket_not_found(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Could not resolve to an issue"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            ticket = tracker.get_ticket("99999")

        assert ticket is None

    def test_get_ticket_invalid_id(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")

        with pytest.raises(RuntimeError, match="Invalid GitHub issue number"):
            tracker.get_ticket("PROJ-123")


class TestGitHubIssuesTrackerListTickets:
    """Tests for list_tickets method."""

    def test_list_tickets_success(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        issues_data = [
            {
                "number": 1,
                "title": "First issue",
                "body": "Desc 1",
                "state": "OPEN",
                "labels": [{"name": "Bug"}],
                "url": "https://github.com/owner/repo/issues/1",
                "assignees": [],
                "milestone": None,
            },
            {
                "number": 2,
                "title": "Second issue",
                "body": "Desc 2",
                "state": "OPEN",
                "labels": [],
                "url": "https://github.com/owner/repo/issues/2",
                "assignees": [],
                "milestone": None,
            },
        ]

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(issues_data)

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            tickets = tracker.list_tickets()

        assert len(tickets) == 2
        assert tickets[0].id == "#1"
        assert tickets[1].id == "#2"

    def test_list_tickets_with_status_filter(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result
        ) as mock_run:
            tracker.list_tickets(status="Done")

        call_args = mock_run.call_args[0][0]
        assert "--state" in call_args
        state_idx = call_args.index("--state")
        assert call_args[state_idx + 1] == "closed"

    def test_list_tickets_with_labels(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result
        ) as mock_run:
            tracker.list_tickets(labels=["Bug", "Frontend"])

        call_args = mock_run.call_args[0][0]
        assert "--label" in call_args
        # Both labels should be present
        label_indices = [i for i, x in enumerate(call_args) if x == "--label"]
        assert len(label_indices) == 2

    def test_list_tickets_with_assignee_me(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "[]"

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result
        ) as mock_run:
            tracker.list_tickets(assignee="me")

        call_args = mock_run.call_args[0][0]
        assert "--assignee" in call_args
        assignee_idx = call_args.index("--assignee")
        assert call_args[assignee_idx + 1] == "@me"

    def test_list_tickets_failure_returns_empty(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            tickets = tracker.list_tickets()

        assert tickets == []


class TestGitHubIssuesTrackerCreateTicket:
    """Tests for create_ticket method."""

    def test_create_ticket_success(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")

        # First call: gh issue create returns URL
        create_result = MagicMock()
        create_result.returncode = 0
        create_result.stdout = "https://github.com/owner/repo/issues/50\n"

        # Second call: gh issue view returns the issue data
        view_result = MagicMock()
        view_result.returncode = 0
        view_result.stdout = json.dumps(
            {
                "number": 50,
                "title": "New feature",
                "body": "Description",
                "state": "OPEN",
                "labels": [{"name": "Feature"}],
                "url": "https://github.com/owner/repo/issues/50",
                "assignees": [],
                "milestone": None,
            }
        )

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run",
            side_effect=[create_result, view_result],
        ):
            ticket = tracker.create_ticket("New feature", "Description", labels=["Feature"])

        assert ticket.id == "#50"
        assert ticket.title == "New feature"

    def test_create_ticket_with_assignee(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")

        create_result = MagicMock()
        create_result.returncode = 0
        create_result.stdout = "https://github.com/owner/repo/issues/51\n"

        view_result = MagicMock()
        view_result.returncode = 0
        view_result.stdout = json.dumps(
            {
                "number": 51,
                "title": "Assigned ticket",
                "body": "Desc",
                "state": "OPEN",
                "labels": [],
                "url": "https://github.com/owner/repo/issues/51",
                "assignees": [{"login": "dev1"}],
                "milestone": None,
            }
        )

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run",
            side_effect=[create_result, view_result],
        ) as mock_run:
            tracker.create_ticket("Assigned ticket", "Desc", assignee="dev1")

        # Verify --assignee was passed to create
        create_call_args = mock_run.call_args_list[0][0][0]
        assert "--assignee" in create_call_args

    def test_create_ticket_failure(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "permission denied"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError):
                tracker.create_ticket("Title", "Description")


class TestGitHubIssuesTrackerUpdateTicket:
    """Tests for update_ticket method."""

    def test_update_ticket_close(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")

        # close call, then view call
        close_result = MagicMock()
        close_result.returncode = 0
        close_result.stdout = ""

        view_result = MagicMock()
        view_result.returncode = 0
        view_result.stdout = json.dumps(
            {
                "number": 10,
                "title": "Issue",
                "body": "",
                "state": "CLOSED",
                "labels": [],
                "url": "https://github.com/owner/repo/issues/10",
                "assignees": [],
                "milestone": None,
            }
        )

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run",
            side_effect=[close_result, view_result],
        ):
            ticket = tracker.update_ticket("10", status="Done")

        assert ticket.status == "Closed"

    def test_update_ticket_title(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")

        edit_result = MagicMock()
        edit_result.returncode = 0
        edit_result.stdout = ""

        view_result = MagicMock()
        view_result.returncode = 0
        view_result.stdout = json.dumps(
            {
                "number": 10,
                "title": "New Title",
                "body": "",
                "state": "OPEN",
                "labels": [],
                "url": "https://github.com/owner/repo/issues/10",
                "assignees": [],
                "milestone": None,
            }
        )

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run",
            side_effect=[edit_result, view_result],
        ) as mock_run:
            ticket = tracker.update_ticket("10", title="New Title")

        assert ticket.title == "New Title"
        edit_call_args = mock_run.call_args_list[0][0][0]
        assert "--title" in edit_call_args

    def test_update_ticket_add_labels(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")

        edit_result = MagicMock()
        edit_result.returncode = 0
        edit_result.stdout = ""

        view_result = MagicMock()
        view_result.returncode = 0
        view_result.stdout = json.dumps(
            {
                "number": 10,
                "title": "Issue",
                "body": "",
                "state": "OPEN",
                "labels": [{"name": "Bug"}],
                "url": "https://github.com/owner/repo/issues/10",
                "assignees": [],
                "milestone": None,
            }
        )

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run",
            side_effect=[edit_result, view_result],
        ) as mock_run:
            tracker.update_ticket("10", labels=["Bug"])

        edit_call_args = mock_run.call_args_list[0][0][0]
        assert "--add-label" in edit_call_args


class TestGitHubIssuesTrackerCommentTicket:
    """Tests for comment_ticket method."""

    def test_comment_success(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result
        ) as mock_run:
            tracker.comment_ticket("42", "Great work!")

        call_args = mock_run.call_args[0][0]
        assert "comment" in call_args
        assert "--body" in call_args

    def test_comment_failure(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "not found"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError):
                tracker.comment_ticket("42", "Comment")


class TestGitHubIssuesTrackerListLabels:
    """Tests for list_labels method."""

    def test_list_labels_success(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        labels_data = [
            {"name": "Bug", "color": "d73a4a", "description": "Something isn't working"},
            {"name": "Feature", "color": "a2eeef", "description": "New feature"},
        ]
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps(labels_data)

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            labels = tracker.list_labels()

        assert len(labels) == 2
        assert labels[0]["name"] == "Bug"
        assert labels[1]["name"] == "Feature"

    def test_list_labels_failure(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "error"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            labels = tracker.list_labels()

        assert labels == []


class TestGitHubIssuesTrackerValidateConfig:
    """Tests for validate_config method."""

    def test_validate_config_valid(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")

        # gh --version succeeds, auth succeeds, repo resolves
        version_result = MagicMock()
        version_result.returncode = 0

        auth_result = MagicMock()
        auth_result.returncode = 0

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run",
            return_value=version_result,
        ):
            valid, issues = tracker.validate_config()

        assert valid is True
        assert issues == []

    def test_validate_config_no_gh_cli(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")

        with patch(
            "lib.vibe.trackers.github_issues.subprocess.run",
            side_effect=FileNotFoundError("gh not found"),
        ):
            valid, issues = tracker.validate_config()

        assert valid is False
        assert any("gh CLI is not installed" in i for i in issues)


class TestGitHubIssuesTrackerNormalizeId:
    """Tests for _normalize_id static method."""

    def test_plain_number(self) -> None:
        assert GitHubIssuesTracker._normalize_id("123") == 123

    def test_hash_prefix(self) -> None:
        assert GitHubIssuesTracker._normalize_id("#456") == 456

    def test_invalid_id(self) -> None:
        with pytest.raises(RuntimeError, match="Invalid GitHub issue number"):
            GitHubIssuesTracker._normalize_id("PROJ-123")


class TestGitHubIssuesTrackerStatusToState:
    """Tests for _status_to_state static method."""

    def test_done_maps_to_closed(self) -> None:
        assert GitHubIssuesTracker._status_to_state("Done") == "closed"

    def test_closed_maps_to_closed(self) -> None:
        assert GitHubIssuesTracker._status_to_state("Closed") == "closed"

    def test_canceled_maps_to_closed(self) -> None:
        assert GitHubIssuesTracker._status_to_state("Canceled") == "closed"

    def test_in_progress_maps_to_open(self) -> None:
        assert GitHubIssuesTracker._status_to_state("In Progress") == "open"

    def test_todo_maps_to_open(self) -> None:
        assert GitHubIssuesTracker._status_to_state("Todo") == "open"

    def test_all_maps_to_all(self) -> None:
        assert GitHubIssuesTracker._status_to_state("all") == "all"


class TestGitHubIssuesTrackerParseIssue:
    """Tests for _parse_issue static method."""

    def test_parse_complete_issue(self) -> None:
        issue = {
            "number": 42,
            "title": "Fix bug",
            "body": "It's broken",
            "state": "OPEN",
            "labels": [{"name": "Bug"}, {"name": "High Risk"}],
            "url": "https://github.com/owner/repo/issues/42",
            "assignees": [{"login": "dev1"}],
            "milestone": None,
        }

        ticket = GitHubIssuesTracker._parse_issue(issue)

        assert ticket.id == "#42"
        assert ticket.title == "Fix bug"
        assert ticket.description == "It's broken"
        assert ticket.status == "Open"
        assert ticket.labels == ["Bug", "High Risk"]
        assert ticket.assignee == "dev1"
        assert ticket.raw == issue

    def test_parse_issue_no_assignee(self) -> None:
        issue = {
            "number": 1,
            "title": "Issue",
            "body": "",
            "state": "CLOSED",
            "labels": [],
            "url": "",
            "assignees": [],
        }

        ticket = GitHubIssuesTracker._parse_issue(issue)

        assert ticket.assignee is None
        assert ticket.status == "Closed"

    def test_parse_issue_null_body(self) -> None:
        issue = {
            "number": 1,
            "title": "Issue",
            "body": None,
            "state": "OPEN",
            "labels": [],
            "url": "",
            "assignees": [],
        }

        ticket = GitHubIssuesTracker._parse_issue(issue)

        assert ticket.description == ""


class TestGitHubIssuesTrackerGetRepo:
    """Tests for _get_repo method."""

    def test_get_repo_from_init(self) -> None:
        tracker = GitHubIssuesTracker(repo="owner/repo")
        assert tracker._get_repo() == "owner/repo"

    def test_get_repo_auto_detect(self) -> None:
        tracker = GitHubIssuesTracker()
        tracker._repo = None

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "detected/repo\n"

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            assert tracker._get_repo() == "detected/repo"

    def test_get_repo_detection_fails(self) -> None:
        tracker = GitHubIssuesTracker()
        tracker._repo = None

        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "not a repo"
        mock_result.stdout = ""

        with patch("lib.vibe.trackers.github_issues.subprocess.run", return_value=mock_result):
            with pytest.raises(RuntimeError, match="Cannot determine GitHub repo"):
                tracker._get_repo()
