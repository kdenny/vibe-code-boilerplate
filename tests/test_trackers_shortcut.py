"""Tests for Shortcut tracker integration."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from lib.vibe.trackers.shortcut import SHORTCUT_API_URL, ShortcutTracker


class TestShortcutTrackerInit:
    """Tests for ShortcutTracker initialization."""

    def test_init_with_api_token(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token_123")
        assert tracker._api_token == "sc_token_123"
        assert tracker._headers["Shortcut-Token"] == "sc_token_123"
        assert tracker._headers["Content-Type"] == "application/json"

    def test_init_with_workspace(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token", workspace="my-workspace")
        assert tracker._workspace == "my-workspace"

    def test_init_from_env(self) -> None:
        with patch.dict("os.environ", {"SHORTCUT_API_TOKEN": "sc_from_env"}):
            tracker = ShortcutTracker()
        assert tracker._api_token == "sc_from_env"

    def test_init_no_token_empty_headers(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            tracker = ShortcutTracker()
        assert tracker._api_token is None
        assert tracker._headers == {}


class TestShortcutTrackerName:
    """Tests for name property."""

    def test_name_returns_shortcut(self) -> None:
        tracker = ShortcutTracker()
        assert tracker.name == "shortcut"


class TestShortcutTrackerAuthenticate:
    """Tests for authenticate method."""

    def test_authenticate_success(self) -> None:
        tracker = ShortcutTracker()
        mock_response = MagicMock()
        mock_response.status_code = 200

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            result = tracker.authenticate(api_token="sc_valid_token")

        assert result is True
        assert tracker._api_token == "sc_valid_token"

    def test_authenticate_failure_unauthorized(self) -> None:
        tracker = ShortcutTracker()
        mock_response = MagicMock()
        mock_response.status_code = 401

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            result = tracker.authenticate(api_token="sc_invalid_token")

        assert result is False

    def test_authenticate_failure_exception(self) -> None:
        tracker = ShortcutTracker()

        with patch("lib.vibe.trackers.shortcut.requests.get", side_effect=Exception("Network error")):
            result = tracker.authenticate(api_token="sc_token")

        assert result is False

    def test_authenticate_no_api_token(self) -> None:
        tracker = ShortcutTracker()
        result = tracker.authenticate()
        assert result is False


class TestShortcutTrackerGetTicket:
    """Tests for get_ticket method."""

    def test_get_ticket_success(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_story = {
            "id": 123,
            "name": "Test Story",
            "description": "Description here",
            "workflow_state": {"name": "In Progress"},
            "labels": [{"name": "Bug"}, {"name": "High Risk"}],
            "app_url": "https://app.shortcut.com/test/story/123",
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_story
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            ticket = tracker.get_ticket("123")

        assert ticket is not None
        assert ticket.id == "SC-123"
        assert ticket.title == "Test Story"
        assert ticket.description == "Description here"
        assert ticket.status == "In Progress"
        assert ticket.labels == ["Bug", "High Risk"]

    def test_get_ticket_with_sc_prefix(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 456, "name": "Story", "workflow_state": {}, "labels": []}
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response) as mock_get:
            tracker.get_ticket("SC-456")

        # Verify the SC- prefix was stripped
        mock_get.assert_called_once()
        call_url = mock_get.call_args[0][0]
        assert "/stories/456" in call_url

    def test_get_ticket_with_hash_prefix(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 789, "name": "Story", "workflow_state": {}, "labels": []}
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response) as mock_get:
            tracker.get_ticket("#789")

        call_url = mock_get.call_args[0][0]
        assert "/stories/789" in call_url

    def test_get_ticket_not_found(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            ticket = tracker.get_ticket("999999")

        assert ticket is None

    def test_get_ticket_exception(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")

        with patch("lib.vibe.trackers.shortcut.requests.get", side_effect=Exception("API error")):
            ticket = tracker.get_ticket("123")

        assert ticket is None


class TestShortcutTrackerListTickets:
    """Tests for list_tickets method."""

    def test_list_tickets_success(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_stories = [
            {
                "id": 1,
                "name": "Story 1",
                "description": "Desc 1",
                "workflow_state": {"name": "To Do"},
                "labels": [],
                "app_url": "https://app.shortcut.com/test/story/1",
            },
            {
                "id": 2,
                "name": "Story 2",
                "description": "Desc 2",
                "workflow_state": {"name": "In Progress"},
                "labels": [{"name": "Feature"}],
                "app_url": "https://app.shortcut.com/test/story/2",
            },
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": mock_stories}
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            tickets = tracker.list_tickets()

        assert len(tickets) == 2
        assert tickets[0].id == "SC-1"
        assert tickets[1].id == "SC-2"
        assert tickets[1].labels == ["Feature"]

    def test_list_tickets_with_status_filter(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response) as mock_get:
            tracker.list_tickets(status="Done")

        call_args = mock_get.call_args
        assert 'state:"Done"' in call_args[1]["params"]["query"]

    def test_list_tickets_with_labels_filter(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response) as mock_get:
            tracker.list_tickets(labels=["Bug", "Critical"])

        call_args = mock_get.call_args
        query = call_args[1]["params"]["query"]
        assert 'label:"Bug"' in query
        assert 'label:"Critical"' in query

    def test_list_tickets_with_limit(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response) as mock_get:
            tracker.list_tickets(limit=10)

        call_args = mock_get.call_args
        assert call_args[1]["params"]["page_size"] == 10

    def test_list_tickets_default_query(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": []}
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response) as mock_get:
            tracker.list_tickets()

        call_args = mock_get.call_args
        query = call_args[1]["params"]["query"]
        assert "!is:done" in query
        assert "!is:archived" in query

    def test_list_tickets_exception_returns_empty(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")

        with patch("lib.vibe.trackers.shortcut.requests.get", side_effect=Exception("API error")):
            tickets = tracker.list_tickets()

        assert tickets == []


class TestShortcutTrackerCreateTicket:
    """Tests for create_ticket method."""

    def test_create_ticket_success(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_story = {
            "id": 100,
            "name": "New Story",
            "description": "New description",
            "workflow_state": {"name": "To Do"},
            "labels": [],
            "app_url": "https://app.shortcut.com/test/story/100",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_story
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.post", return_value=mock_response):
            ticket = tracker.create_ticket("New Story", "New description")

        assert ticket.id == "SC-100"
        assert ticket.title == "New Story"

    def test_create_ticket_with_labels(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_story = {
            "id": 101,
            "name": "Labeled Story",
            "description": "Description",
            "workflow_state": {"name": "To Do"},
            "labels": [{"name": "Bug"}],
            "app_url": "https://app.shortcut.com/test/story/101",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_story
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.post", return_value=mock_response), patch.object(
            tracker, "_get_label_ids", return_value=[1]
        ) as mock_labels:
            ticket = tracker.create_ticket("Labeled Story", "Description", labels=["Bug"])

        mock_labels.assert_called_once_with(["Bug"])
        assert ticket.labels == ["Bug"]

    def test_create_ticket_failure(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")

        with patch("lib.vibe.trackers.shortcut.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to create ticket"):
                tracker.create_ticket("Title", "Description")


class TestShortcutTrackerUpdateTicket:
    """Tests for update_ticket method."""

    def test_update_ticket_title(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_story = {
            "id": 123,
            "name": "Updated Title",
            "description": "Desc",
            "workflow_state": {"name": "To Do"},
            "labels": [],
            "app_url": "https://app.shortcut.com/test/story/123",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_story
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.put", return_value=mock_response):
            ticket = tracker.update_ticket("123", title="Updated Title")

        assert ticket.title == "Updated Title"

    def test_update_ticket_status(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_story = {
            "id": 123,
            "name": "Story",
            "description": "Desc",
            "workflow_state": {"name": "Done"},
            "labels": [],
            "app_url": "https://app.shortcut.com/test/story/123",
        }
        mock_response = MagicMock()
        mock_response.json.return_value = mock_story
        mock_response.raise_for_status = MagicMock()

        with patch.object(tracker, "_get_workflow_state_id", return_value=500001):
            with patch("lib.vibe.trackers.shortcut.requests.put", return_value=mock_response) as mock_put:
                ticket = tracker.update_ticket("123", status="Done")

        call_args = mock_put.call_args
        assert call_args[1]["json"]["workflow_state_id"] == 500001
        assert ticket.status == "Done"

    def test_update_ticket_status_invalid_state(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")

        with patch.object(tracker, "_get_workflow_state_id", return_value=None):
            with pytest.raises(RuntimeError, match="No workflow state named 'InvalidState'"):
                tracker.update_ticket("123", status="InvalidState")

    def test_update_ticket_failure(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch("lib.vibe.trackers.shortcut.requests.put", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to update ticket"):
                tracker.update_ticket("123", title="New Title")


class TestShortcutTrackerCommentTicket:
    """Tests for comment_ticket method."""

    def test_comment_ticket_success(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.post", return_value=mock_response) as mock_post:
            tracker.comment_ticket("SC-123", "This is a comment")

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "/stories/123/comments" in call_args[0][0]
        assert call_args[1]["json"]["text"] == "This is a comment"

    def test_comment_ticket_failure(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch("lib.vibe.trackers.shortcut.requests.post", return_value=mock_response):
            with pytest.raises(RuntimeError, match="Failed to add comment"):
                tracker.comment_ticket("123", "Comment")


class TestShortcutTrackerValidateConfig:
    """Tests for validate_config method."""

    def test_validate_config_valid(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")

        with patch.object(tracker, "authenticate", return_value=True):
            valid, issues = tracker.validate_config()

        assert valid is True
        assert issues == []

    def test_validate_config_no_api_token(self) -> None:
        tracker = ShortcutTracker()
        tracker._api_token = None

        valid, issues = tracker.validate_config()

        assert valid is False
        assert "SHORTCUT_API_TOKEN not set" in issues

    def test_validate_config_invalid_token(self) -> None:
        tracker = ShortcutTracker(api_token="sc_invalid")

        with patch.object(tracker, "authenticate", return_value=False):
            valid, issues = tracker.validate_config()

        assert valid is False
        assert "SHORTCUT_API_TOKEN is invalid or expired" in issues


class TestShortcutTrackerGetLabelIds:
    """Tests for _get_label_ids method."""

    def test_get_label_ids_success(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_labels = [
            {"id": 1, "name": "Bug"},
            {"id": 2, "name": "Feature"},
            {"id": 3, "name": "Chore"},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_labels
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            label_ids = tracker._get_label_ids(["Bug", "Feature"])

        assert label_ids == [1, 2]

    def test_get_label_ids_case_insensitive(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_labels = [{"id": 1, "name": "Bug"}]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_labels
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            label_ids = tracker._get_label_ids(["BUG"])

        assert label_ids == [1]

    def test_get_label_ids_partial_match(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_labels = [{"id": 1, "name": "Bug"}]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_labels
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            label_ids = tracker._get_label_ids(["Bug", "NonexistentLabel"])

        assert label_ids == [1]

    def test_get_label_ids_empty_list(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        label_ids = tracker._get_label_ids([])
        assert label_ids == []

    def test_get_label_ids_exception(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")

        with patch("lib.vibe.trackers.shortcut.requests.get", side_effect=Exception("API error")):
            label_ids = tracker._get_label_ids(["Bug"])

        assert label_ids == []


class TestShortcutTrackerListLabels:
    """Tests for list_labels method."""

    def test_list_labels_success(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_labels = [
            {"id": 1, "name": "Bug", "color": "#ff0000"},
            {"id": 2, "name": "Feature", "color": "#00ff00"},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_labels
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            labels = tracker.list_labels()

        assert len(labels) == 2
        assert labels[0] == {"id": "1", "name": "Bug", "color": "#ff0000"}
        assert labels[1] == {"id": "2", "name": "Feature", "color": "#00ff00"}

    def test_list_labels_exception(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")

        with patch("lib.vibe.trackers.shortcut.requests.get", side_effect=Exception("API error")):
            labels = tracker.list_labels()

        assert labels == []


class TestShortcutTrackerGetWorkflowStateId:
    """Tests for _get_workflow_state_id method."""

    def test_get_workflow_state_id_success(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_workflows = [
            {
                "id": 1,
                "name": "Engineering",
                "states": [
                    {"id": 500001, "name": "Backlog"},
                    {"id": 500002, "name": "To Do"},
                    {"id": 500003, "name": "In Progress"},
                    {"id": 500004, "name": "Done"},
                ],
            }
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_workflows
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            state_id = tracker._get_workflow_state_id("Done")

        assert state_id == 500004

    def test_get_workflow_state_id_case_insensitive(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_workflows = [{"id": 1, "name": "Workflow", "states": [{"id": 500001, "name": "In Progress"}]}]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_workflows
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            state_id = tracker._get_workflow_state_id("in progress")

        assert state_id == 500001

    def test_get_workflow_state_id_multiple_workflows(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_workflows = [
            {"id": 1, "name": "Workflow 1", "states": [{"id": 100, "name": "Backlog"}]},
            {"id": 2, "name": "Workflow 2", "states": [{"id": 200, "name": "Done"}]},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_workflows
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            state_id = tracker._get_workflow_state_id("Done")

        assert state_id == 200

    def test_get_workflow_state_id_not_found(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")
        mock_workflows = [{"id": 1, "name": "Workflow", "states": [{"id": 500001, "name": "To Do"}]}]
        mock_response = MagicMock()
        mock_response.json.return_value = mock_workflows
        mock_response.raise_for_status = MagicMock()

        with patch("lib.vibe.trackers.shortcut.requests.get", return_value=mock_response):
            state_id = tracker._get_workflow_state_id("NonexistentState")

        assert state_id is None

    def test_get_workflow_state_id_exception(self) -> None:
        tracker = ShortcutTracker(api_token="sc_token")

        with patch("lib.vibe.trackers.shortcut.requests.get", side_effect=Exception("API error")):
            state_id = tracker._get_workflow_state_id("Done")

        assert state_id is None


class TestShortcutTrackerParseStory:
    """Tests for _parse_story method."""

    def test_parse_story_complete(self) -> None:
        tracker = ShortcutTracker()
        story = {
            "id": 123,
            "name": "Test Story",
            "description": "Test description",
            "workflow_state": {"name": "In Progress"},
            "labels": [{"name": "Bug"}, {"name": "High Risk"}],
            "app_url": "https://app.shortcut.com/test/story/123",
        }

        ticket = tracker._parse_story(story)

        assert ticket.id == "SC-123"
        assert ticket.title == "Test Story"
        assert ticket.description == "Test description"
        assert ticket.status == "In Progress"
        assert ticket.labels == ["Bug", "High Risk"]
        assert ticket.url == "https://app.shortcut.com/test/story/123"
        assert ticket.raw == story

    def test_parse_story_no_workflow_state(self) -> None:
        tracker = ShortcutTracker()
        story = {
            "id": 456,
            "name": "Story without state",
            "description": "",
            "workflow_state": {},
            "labels": [],
            "app_url": "",
        }

        ticket = tracker._parse_story(story)

        assert ticket.status == ""

    def test_parse_story_no_id(self) -> None:
        tracker = ShortcutTracker()
        story = {
            "name": "Story without ID",
            "description": "",
            "workflow_state": {"name": "To Do"},
            "labels": [],
            "app_url": "",
        }

        ticket = tracker._parse_story(story)

        assert ticket.id == ""

    def test_parse_story_empty_labels(self) -> None:
        tracker = ShortcutTracker()
        story = {
            "id": 789,
            "name": "Story",
            "description": "",
            "workflow_state": {"name": "To Do"},
            "labels": [],
            "app_url": "",
        }

        ticket = tracker._parse_story(story)

        assert ticket.labels == []
