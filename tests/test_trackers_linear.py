"""Tests for Linear tracker integration."""

from unittest.mock import MagicMock, patch

import pytest

from lib.vibe.trackers.linear import LINEAR_API_URL, LinearTracker


class TestLinearTrackerInit:
    """Tests for LinearTracker initialization."""

    def test_init_with_api_key(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key-not-real")
        assert tracker._api_key == "test-fake-key-not-real"
        assert tracker._headers["Authorization"] == "test-fake-key-not-real"
        assert tracker._headers["Content-Type"] == "application/json"

    def test_init_with_team_id(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key", team_id="team_abc")
        assert tracker._team_id == "team_abc"

    def test_init_from_env(self) -> None:
        with patch.dict("os.environ", {"LINEAR_API_KEY": "test-key-from-env"}):
            tracker = LinearTracker()
        assert tracker._api_key == "test-key-from-env"

    def test_init_no_key_empty_headers(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            tracker = LinearTracker()
        assert tracker._api_key is None
        assert tracker._headers == {}


class TestLinearTrackerName:
    """Tests for name property."""

    def test_name_returns_linear(self) -> None:
        tracker = LinearTracker()
        assert tracker.name == "linear"


class TestLinearTrackerAuthenticate:
    """Tests for authenticate method."""

    def test_authenticate_success(self) -> None:
        tracker = LinearTracker()
        mock_response = {"data": {"viewer": {"id": "user123", "name": "Test User"}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            result = tracker.authenticate(api_key="test-valid-key")

        assert result is True
        assert tracker._api_key == "test-valid-key"

    def test_authenticate_failure_no_viewer(self) -> None:
        tracker = LinearTracker()
        mock_response = {"data": {}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            result = tracker.authenticate(api_key="test-invalid-key")  # noqa: S106

        assert result is False

    def test_authenticate_failure_exception(self) -> None:
        tracker = LinearTracker()

        with patch.object(tracker, "_execute_query", side_effect=Exception("API error")):
            result = tracker.authenticate(api_key="test-error-key")  # noqa: S106

        assert result is False

    def test_authenticate_no_api_key(self) -> None:
        tracker = LinearTracker()
        result = tracker.authenticate()
        assert result is False


class TestLinearTrackerExecuteQuery:
    """Tests for _execute_query method."""

    def test_execute_query_success(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"viewer": {"id": "123"}}}
        mock_response.raise_for_status = MagicMock()

        with patch(
            "lib.vibe.trackers.linear.requests.post", return_value=mock_response
        ) as mock_post:
            result = tracker._execute_query("query { viewer { id } }")

        mock_post.assert_called_once_with(
            LINEAR_API_URL,
            headers=tracker._headers,
            json={"query": "query { viewer { id } }"},
            timeout=30,
        )
        assert result == {"data": {"viewer": {"id": "123"}}}

    def test_execute_query_with_variables(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": {"issue": {"id": "abc"}}}
        mock_response.raise_for_status = MagicMock()

        with patch(
            "lib.vibe.trackers.linear.requests.post", return_value=mock_response
        ) as mock_post:
            _result = tracker._execute_query(
                "query GetIssue($id: String!) { issue(id: $id) { id } }", {"id": "TEST-1"}
            )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[1]["json"]["variables"] == {"id": "TEST-1"}


class TestLinearTrackerGetTicket:
    """Tests for get_ticket method."""

    def test_get_ticket_success(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_issue = {
            "id": "uuid-123",
            "identifier": "TEST-1",
            "title": "Test Issue",
            "description": "Description here",
            "state": {"id": "state1", "name": "Todo"},
            "team": {"id": "team123"},
            "labels": {"nodes": [{"name": "Bug"}, {"name": "High Risk"}]},
            "url": "https://linear.app/test/issue/TEST-1",
        }
        mock_response = {"data": {"issue": mock_issue}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            ticket = tracker.get_ticket("TEST-1")

        assert ticket is not None
        assert ticket.id == "TEST-1"
        assert ticket.title == "Test Issue"
        assert ticket.description == "Description here"
        assert ticket.status == "Todo"
        assert ticket.labels == ["Bug", "High Risk"]
        assert ticket.url == "https://linear.app/test/issue/TEST-1"

    def test_get_ticket_not_found(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_response = {"data": {"issue": None}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            ticket = tracker.get_ticket("NONEXISTENT-999")

        assert ticket is None

    def test_get_ticket_exception(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")

        with patch.object(tracker, "_execute_query", side_effect=Exception("API error")):
            ticket = tracker.get_ticket("TEST-1")

        assert ticket is None


class TestLinearTrackerListTickets:
    """Tests for list_tickets method."""

    def test_list_tickets_success(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_issues = [
            {
                "id": "uuid-1",
                "identifier": "TEST-1",
                "title": "Issue 1",
                "description": "Desc 1",
                "state": {"name": "Todo"},
                "labels": {"nodes": []},
                "url": "https://linear.app/test/issue/TEST-1",
            },
            {
                "id": "uuid-2",
                "identifier": "TEST-2",
                "title": "Issue 2",
                "description": "Desc 2",
                "state": {"name": "In Progress"},
                "labels": {"nodes": [{"name": "Feature"}]},
                "url": "https://linear.app/test/issue/TEST-2",
            },
        ]
        mock_response = {"data": {"issues": {"nodes": mock_issues}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            tickets = tracker.list_tickets()

        assert len(tickets) == 2
        assert tickets[0].id == "TEST-1"
        assert tickets[1].id == "TEST-2"
        assert tickets[1].labels == ["Feature"]

    def test_list_tickets_with_status_filter(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_response = {"data": {"issues": {"nodes": []}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response) as mock_query:
            tracker.list_tickets(status="Todo")

        call_args = mock_query.call_args
        variables = call_args[0][1]
        assert variables["filter"]["state"] == {"name": {"eq": "Todo"}}

    def test_list_tickets_with_label_filter(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_response = {"data": {"issues": {"nodes": []}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response) as mock_query:
            tracker.list_tickets(labels=["Bug", "Feature"])

        call_args = mock_query.call_args
        variables = call_args[0][1]
        assert variables["filter"]["labels"] == {"name": {"in": ["Bug", "Feature"]}}

    def test_list_tickets_with_team_filter(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key", team_id="team_abc")
        mock_response = {"data": {"issues": {"nodes": []}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response) as mock_query:
            tracker.list_tickets()

        call_args = mock_query.call_args
        variables = call_args[0][1]
        assert variables["filter"]["team"] == {"id": {"eq": "team_abc"}}

    def test_list_tickets_with_limit(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_response = {"data": {"issues": {"nodes": []}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response) as mock_query:
            tracker.list_tickets(limit=10)

        call_args = mock_query.call_args
        variables = call_args[0][1]
        assert variables["first"] == 10

    def test_list_tickets_exception_returns_empty(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")

        with patch.object(tracker, "_execute_query", side_effect=Exception("API error")):
            tickets = tracker.list_tickets()

        assert tickets == []


class TestLinearTrackerCreateTicket:
    """Tests for create_ticket method."""

    def test_create_ticket_success(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key", team_id="team_abc")
        mock_issue = {
            "id": "uuid-new",
            "identifier": "TEST-100",
            "title": "New Issue",
            "description": "New description",
            "state": {"name": "Backlog"},
            "labels": {"nodes": []},
            "url": "https://linear.app/test/issue/TEST-100",
        }
        mock_response = {"data": {"issueCreate": {"success": True, "issue": mock_issue}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            ticket = tracker.create_ticket("New Issue", "New description")

        assert ticket.id == "TEST-100"
        assert ticket.title == "New Issue"

    def test_create_ticket_with_labels(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key", team_id="team_abc")
        mock_issue = {
            "id": "uuid-new",
            "identifier": "TEST-101",
            "title": "Labeled Issue",
            "description": "Description",
            "state": {"name": "Backlog"},
            "labels": {"nodes": [{"name": "Bug"}]},
            "url": "https://linear.app/test/issue/TEST-101",
        }
        mock_response = {"data": {"issueCreate": {"success": True, "issue": mock_issue}}}

        with (
            patch.object(tracker, "_execute_query", return_value=mock_response),
            patch.object(tracker, "_get_label_ids", return_value=["label-id-1"]) as mock_labels,
        ):
            ticket = tracker.create_ticket("Labeled Issue", "Description", labels=["Bug"])

        mock_labels.assert_called_once_with("team_abc", ["Bug"])
        assert ticket.labels == ["Bug"]

    def test_create_ticket_failure(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key", team_id="team_abc")
        mock_response = {"data": {"issueCreate": {"success": False, "issue": None}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to create ticket"):
                tracker.create_ticket("Title", "Description")


class TestLinearTrackerUpdateTicket:
    """Tests for update_ticket method."""

    def test_update_ticket_title(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_issue = {
            "id": "uuid-1",
            "identifier": "TEST-1",
            "title": "Updated Title",
            "description": "Desc",
            "state": {"name": "Todo"},
            "labels": {"nodes": []},
            "url": "https://linear.app/test/issue/TEST-1",
        }
        mock_response = {"data": {"issueUpdate": {"success": True, "issue": mock_issue}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            ticket = tracker.update_ticket("TEST-1", title="Updated Title")

        assert ticket.title == "Updated Title"

    def test_update_ticket_status(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        # First call returns the current ticket, second call is the update
        mock_current_issue = {
            "id": "uuid-1",
            "identifier": "TEST-1",
            "title": "Title",
            "description": "Desc",
            "state": {"id": "state-todo", "name": "Todo"},
            "team": {"id": "team_abc"},
            "labels": {"nodes": []},
            "url": "https://linear.app/test/issue/TEST-1",
        }
        mock_updated_issue = {
            "id": "uuid-1",
            "identifier": "TEST-1",
            "title": "Title",
            "description": "Desc",
            "state": {"name": "Done"},
            "labels": {"nodes": []},
            "url": "https://linear.app/test/issue/TEST-1",
        }

        with patch.object(tracker, "get_ticket") as mock_get:
            mock_get.return_value = tracker._parse_issue(mock_current_issue)
            with patch.object(tracker, "_get_workflow_state_id", return_value="state-done"):
                with patch.object(
                    tracker,
                    "_execute_query",
                    return_value={
                        "data": {"issueUpdate": {"success": True, "issue": mock_updated_issue}}
                    },
                ):
                    ticket = tracker.update_ticket("TEST-1", status="Done")

        assert ticket.status == "Done"

    def test_update_ticket_status_not_found(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")

        with patch.object(tracker, "get_ticket", return_value=None):
            with pytest.raises(RuntimeError, match="Ticket not found"):
                tracker.update_ticket("NONEXISTENT-999", status="Done")

    def test_update_ticket_status_no_team(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_issue = {
            "id": "uuid-1",
            "identifier": "TEST-1",
            "title": "Title",
            "description": "Desc",
            "state": {"name": "Todo"},
            "team": None,
            "labels": {"nodes": []},
            "url": "https://linear.app/test/issue/TEST-1",
        }

        with patch.object(tracker, "get_ticket") as mock_get:
            mock_get.return_value = tracker._parse_issue(mock_issue)
            with pytest.raises(RuntimeError, match="Cannot resolve status: issue has no team"):
                tracker.update_ticket("TEST-1", status="Done")

    def test_update_ticket_status_invalid_state(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_issue = {
            "id": "uuid-1",
            "identifier": "TEST-1",
            "title": "Title",
            "description": "Desc",
            "state": {"name": "Todo"},
            "team": {"id": "team_abc"},
            "labels": {"nodes": []},
            "url": "https://linear.app/test/issue/TEST-1",
        }

        with patch.object(tracker, "get_ticket") as mock_get:
            mock_get.return_value = tracker._parse_issue(mock_issue)
            with patch.object(tracker, "_get_workflow_state_id", return_value=None):
                with pytest.raises(RuntimeError, match="No workflow state named 'InvalidState'"):
                    tracker.update_ticket("TEST-1", status="InvalidState")

    def test_update_ticket_failure(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_response = {"data": {"issueUpdate": {"success": False, "issue": None}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to update ticket"):
                tracker.update_ticket("TEST-1", title="New Title")


class TestLinearTrackerCommentTicket:
    """Tests for comment_ticket method."""

    def test_comment_ticket_success(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_issue = {
            "id": "uuid-1",
            "identifier": "TEST-1",
            "title": "Title",
            "description": "Desc",
            "state": {"name": "Todo"},
            "labels": {"nodes": []},
            "url": "https://linear.app/test/issue/TEST-1",
        }
        mock_comment_response = {
            "data": {"commentCreate": {"success": True, "comment": {"id": "comment-1"}}}
        }

        with patch.object(tracker, "get_ticket") as mock_get:
            mock_get.return_value = tracker._parse_issue(mock_issue)
            with patch.object(
                tracker, "_execute_query", return_value=mock_comment_response
            ) as mock_query:
                tracker.comment_ticket("TEST-1", "This is a comment")

        # Verify the comment mutation was called
        call_args = mock_query.call_args
        variables = call_args[0][1]
        assert variables["input"]["issueId"] == "uuid-1"
        assert variables["input"]["body"] == "This is a comment"

    def test_comment_ticket_not_found(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")

        with patch.object(tracker, "get_ticket", return_value=None):
            with pytest.raises(RuntimeError, match="Ticket not found"):
                tracker.comment_ticket("NONEXISTENT-999", "Comment")

    def test_comment_ticket_no_issue_id(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_issue = {
            "id": None,
            "identifier": "TEST-1",
            "title": "Title",
            "description": "Desc",
            "state": {"name": "Todo"},
            "labels": {"nodes": []},
            "url": "https://linear.app/test/issue/TEST-1",
        }

        with patch.object(tracker, "get_ticket") as mock_get:
            mock_get.return_value = tracker._parse_issue(mock_issue)
            with pytest.raises(RuntimeError, match="Cannot comment: issue has no id"):
                tracker.comment_ticket("TEST-1", "Comment")


class TestLinearTrackerValidateConfig:
    """Tests for validate_config method."""

    def test_validate_config_valid(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key", team_id="team_abc")

        with patch.object(tracker, "authenticate", return_value=True):
            valid, issues = tracker.validate_config()

        assert valid is True
        assert issues == []

    def test_validate_config_no_api_key(self) -> None:
        tracker = LinearTracker(team_id="team_abc")
        tracker._api_key = None

        valid, issues = tracker.validate_config()

        assert valid is False
        assert "LINEAR_API_KEY not set" in issues

    def test_validate_config_no_team_id(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")

        with patch.object(tracker, "authenticate", return_value=True):
            valid, issues = tracker.validate_config()

        assert valid is False
        assert "Linear team ID not configured" in issues

    def test_validate_config_invalid_key(self) -> None:
        tracker = LinearTracker(api_key="test-invalid-key", team_id="team_abc")

        with patch.object(tracker, "authenticate", return_value=False):
            valid, issues = tracker.validate_config()

        assert valid is False
        assert "LINEAR_API_KEY is invalid or expired" in issues


class TestLinearTrackerGetLabelIds:
    """Tests for _get_label_ids method."""

    def test_get_label_ids_success(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_labels = [
            {"id": "label-1", "name": "Bug"},
            {"id": "label-2", "name": "Feature"},
            {"id": "label-3", "name": "Chore"},
        ]
        mock_response = {"data": {"team": {"labels": {"nodes": mock_labels}}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            label_ids = tracker._get_label_ids("team_abc", ["Bug", "Feature"])

        assert label_ids == ["label-1", "label-2"]

    def test_get_label_ids_partial_match(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_labels = [{"id": "label-1", "name": "Bug"}]
        mock_response = {"data": {"team": {"labels": {"nodes": mock_labels}}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            label_ids = tracker._get_label_ids("team_abc", ["Bug", "NonexistentLabel"])

        assert label_ids == ["label-1"]

    def test_get_label_ids_no_team(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        label_ids = tracker._get_label_ids(None, ["Bug"])
        assert label_ids == []

    def test_get_label_ids_no_labels(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        label_ids = tracker._get_label_ids("team_abc", [])
        assert label_ids == []

    def test_get_label_ids_exception(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")

        with patch.object(tracker, "_execute_query", side_effect=Exception("API error")):
            label_ids = tracker._get_label_ids("team_abc", ["Bug"])

        assert label_ids == []


class TestLinearTrackerListLabels:
    """Tests for list_labels method."""

    def test_list_labels_success(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key", team_id="team_abc")
        mock_labels = [
            {"id": "label-1", "name": "Bug", "color": "#ff0000"},
            {"id": "label-2", "name": "Feature", "color": "#00ff00"},
        ]
        mock_response = {"data": {"issueLabels": {"nodes": mock_labels}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            labels = tracker.list_labels()

        assert len(labels) == 2
        assert labels[0] == {"id": "label-1", "name": "Bug", "color": "#ff0000"}
        assert labels[1] == {"id": "label-2", "name": "Feature", "color": "#00ff00"}

    def test_list_labels_no_team(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_response = {"data": {"issueLabels": {"nodes": []}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response) as mock_query:
            tracker.list_labels()

        # Should pass None for variables when no team_id
        call_args = mock_query.call_args
        assert call_args[0][1] is None

    def test_list_labels_exception(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")

        with patch.object(tracker, "_execute_query", side_effect=Exception("API error")):
            labels = tracker.list_labels()

        assert labels == []


class TestLinearTrackerGetWorkflowStateId:
    """Tests for _get_workflow_state_id method."""

    def test_get_workflow_state_id_success(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_states = [
            {"id": "state-1", "name": "Backlog"},
            {"id": "state-2", "name": "Todo"},
            {"id": "state-3", "name": "In Progress"},
            {"id": "state-4", "name": "Done"},
        ]
        mock_response = {"data": {"team": {"states": {"nodes": mock_states}}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            state_id = tracker._get_workflow_state_id("team_abc", "Done")

        assert state_id == "state-4"

    def test_get_workflow_state_id_case_insensitive(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_states = [{"id": "state-1", "name": "In Progress"}]
        mock_response = {"data": {"team": {"states": {"nodes": mock_states}}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            state_id = tracker._get_workflow_state_id("team_abc", "in progress")

        assert state_id == "state-1"

    def test_get_workflow_state_id_not_found(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")
        mock_states = [{"id": "state-1", "name": "Todo"}]
        mock_response = {"data": {"team": {"states": {"nodes": mock_states}}}}

        with patch.object(tracker, "_execute_query", return_value=mock_response):
            state_id = tracker._get_workflow_state_id("team_abc", "NonexistentState")

        assert state_id is None

    def test_get_workflow_state_id_exception(self) -> None:
        tracker = LinearTracker(api_key="test-fake-key")

        with patch.object(tracker, "_execute_query", side_effect=Exception("API error")):
            state_id = tracker._get_workflow_state_id("team_abc", "Done")

        assert state_id is None


class TestLinearTrackerParseIssue:
    """Tests for _parse_issue method."""

    def test_parse_issue_complete(self) -> None:
        tracker = LinearTracker()
        issue = {
            "id": "uuid-123",
            "identifier": "TEST-1",
            "title": "Test Issue",
            "description": "Test description",
            "state": {"name": "In Progress"},
            "labels": {"nodes": [{"name": "Bug"}, {"name": "High Risk"}]},
            "url": "https://linear.app/test/issue/TEST-1",
        }

        ticket = tracker._parse_issue(issue)

        assert ticket.id == "TEST-1"
        assert ticket.title == "Test Issue"
        assert ticket.description == "Test description"
        assert ticket.status == "In Progress"
        assert ticket.labels == ["Bug", "High Risk"]
        assert ticket.url == "https://linear.app/test/issue/TEST-1"
        assert ticket.raw == issue

    def test_parse_issue_missing_identifier_uses_id(self) -> None:
        tracker = LinearTracker()
        issue = {
            "id": "uuid-456",
            "title": "Issue without identifier",
            "description": "",
            "state": {"name": "Todo"},
            "labels": {"nodes": []},
            "url": "",
        }

        ticket = tracker._parse_issue(issue)

        assert ticket.id == "uuid-456"

    def test_parse_issue_no_state(self) -> None:
        tracker = LinearTracker()
        issue = {
            "id": "uuid-789",
            "identifier": "TEST-2",
            "title": "Issue",
            "description": "",
            "state": None,
            "labels": {"nodes": []},
            "url": "",
        }

        ticket = tracker._parse_issue(issue)

        assert ticket.status == ""

    def test_parse_issue_empty_labels(self) -> None:
        tracker = LinearTracker()
        issue = {
            "id": "uuid-abc",
            "identifier": "TEST-3",
            "title": "Issue",
            "description": "",
            "state": {"name": "Todo"},
            "labels": {"nodes": []},
            "url": "",
        }

        ticket = tracker._parse_issue(issue)

        assert ticket.labels == []

    def test_parse_issue_missing_labels_key(self) -> None:
        tracker = LinearTracker()
        issue = {
            "id": "uuid-def",
            "identifier": "TEST-4",
            "title": "Issue",
            "description": "",
            "state": {"name": "Todo"},
            "url": "",
        }

        ticket = tracker._parse_issue(issue)

        assert ticket.labels == []
