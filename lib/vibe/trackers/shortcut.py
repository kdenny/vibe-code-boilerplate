"""Shortcut.com ticket tracker integration."""

import os
from typing import Any

import requests

from lib.vibe.trackers.base import Ticket, TrackerBase
from lib.vibe.utils.retry import with_retry

SHORTCUT_API_URL = "https://api.app.shortcut.com/api/v3"


class ShortcutTracker(TrackerBase):
    """
    Shortcut.com integration.

    Uses the Shortcut REST API v3.
    API Reference: https://developer.shortcut.com/api/rest/v3
    """

    def __init__(self, api_token: str | None = None, workspace: str | None = None):
        self._api_token = api_token or os.environ.get("SHORTCUT_API_TOKEN")
        self._workspace = workspace
        self._headers: dict[str, str] = {}
        if self._api_token:
            self._headers = {
                "Shortcut-Token": self._api_token,
                "Content-Type": "application/json",
            }

    @property
    def name(self) -> str:
        return "shortcut"

    @with_retry()
    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        """Make an API request with retry logic."""
        url = f"{SHORTCUT_API_URL}{path}"
        response = requests.request(method, url, headers=self._headers, timeout=30, **kwargs)
        response.raise_for_status()
        return response

    def authenticate(self, **kwargs: Any) -> bool:
        """Authenticate with Shortcut API."""
        api_token = kwargs.get("api_token") or self._api_token
        if not api_token:
            return False

        self._api_token = api_token
        self._headers = {
            "Shortcut-Token": api_token,
            "Content-Type": "application/json",
        }

        # Test authentication by fetching current member
        try:
            response = self._request("GET", "/member")
            return bool(response.status_code == 200)
        except requests.RequestException:
            return False

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Fetch a single story by ID."""
        # Shortcut story IDs are numeric
        story_id = ticket_id.lstrip("SC-").lstrip("#")
        try:
            response = self._request("GET", f"/stories/{story_id}")
            story = response.json()
            return self._parse_story(story)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                return None
            return None
        except requests.RequestException:
            return None

    def list_tickets(
        self,
        status: str | None = None,
        labels: list[str] | None = None,
        limit: int = 50,
    ) -> list[Ticket]:
        """List stories with optional filters using search, with pagination."""
        # Build search query
        query_parts = []

        if status:
            # Map common status names to Shortcut workflow states
            query_parts.append(f'state:"{status}"')

        if labels:
            for label in labels:
                query_parts.append(f'label:"{label}"')

        # Default: search for open stories
        if not query_parts:
            query_parts.append("!is:done !is:archived")

        search_query = " ".join(query_parts)

        all_tickets: list[Ticket] = []
        page_size = min(limit, 25)  # Shortcut default page size
        next_token: str | None = None

        try:
            while True:
                params: dict[str, Any] = {"query": search_query, "page_size": page_size}
                if next_token:
                    params["next"] = next_token

                response = self._request(
                    "GET",
                    "/search/stories",
                    params=params,
                )
                data = response.json()
                stories = data.get("data", [])

                all_tickets.extend(self._parse_story(story) for story in stories)

                if len(all_tickets) >= limit:
                    return all_tickets[:limit]

                next_token = data.get("next")
                if not next_token:
                    break

            return all_tickets
        except requests.RequestException:
            return all_tickets  # Return what we have so far

    def create_ticket(
        self,
        title: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Create a new story in Shortcut."""
        payload: dict[str, Any] = {
            "name": title,
            "description": description,
            "story_type": "feature",
        }

        # If labels provided, resolve or create matching label IDs
        if labels:
            label_ids = self._get_or_create_label_ids(labels)
            if label_ids:
                payload["labels"] = [{"id": lid} for lid in label_ids]

        try:
            response = self._request("POST", "/stories", json=payload)
            story = response.json()
            return self._parse_story(story)
        except requests.HTTPError as e:
            raise RuntimeError(f"Failed to create ticket: {e}") from e

    def update_ticket(
        self,
        ticket_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Update an existing story."""
        story_id = ticket_id.lstrip("SC-").lstrip("#")
        payload: dict[str, Any] = {}

        if title:
            payload["name"] = title
        if description:
            payload["description"] = description
        if status:
            # Need to resolve workflow state ID
            state_id = self._get_workflow_state_id(status)
            if not state_id:
                raise RuntimeError(
                    f"No workflow state named '{status}'. "
                    "Check state name in Shortcut (e.g., Done, In Progress)."
                )
            payload["workflow_state_id"] = state_id
        if labels:
            label_ids = self._get_or_create_label_ids(labels)
            if label_ids:
                payload["labels"] = [{"id": lid} for lid in label_ids]

        try:
            response = self._request("PUT", f"/stories/{story_id}", json=payload)
            story = response.json()
            return self._parse_story(story)
        except requests.HTTPError as e:
            raise RuntimeError(f"Failed to update ticket: {e}") from e

    def comment_ticket(self, ticket_id: str, body: str) -> None:
        """Add a comment to a story."""
        story_id = ticket_id.lstrip("SC-").lstrip("#")
        try:
            self._request("POST", f"/stories/{story_id}/comments", json={"text": body})
        except requests.HTTPError as e:
            raise RuntimeError(f"Failed to add comment: {e}") from e

    def set_parent(self, ticket_id: str, parent_id: str) -> None:
        """Set a parent (epic) relationship for a Shortcut story.

        In Shortcut, the parent concept maps to epics. This method sets
        the epic_id on the story to create a parent-child relationship.

        Args:
            ticket_id: The child story identifier (e.g. "SC-101")
            parent_id: The parent epic/story identifier (e.g. "SC-100")
        """
        story_id = ticket_id.lstrip("SC-").lstrip("#")
        parent_story_id = parent_id.lstrip("SC-").lstrip("#")

        try:
            # Try to set as epic relationship first
            self._request(
                "PUT",
                f"/stories/{story_id}",
                json={"epic_id": int(parent_story_id)},
            )
        except (requests.HTTPError, ValueError):
            # If epic_id doesn't work (parent is a story, not an epic),
            # fall back to creating a story link
            try:
                self._request(
                    "POST",
                    f"/stories/{story_id}/story-links",
                    json={
                        "object_id": int(parent_story_id),
                        "verb": "blocks",
                    },
                )
            except requests.HTTPError as link_err:
                raise RuntimeError(f"Failed to set parent relationship: {link_err}") from link_err

    def add_relation(self, ticket_id: str, related_id: str, relation_type: str = "related") -> None:
        """Create a non-hierarchical relationship between two Shortcut stories.

        Uses story links to create the relationship.

        Args:
            ticket_id: First story identifier
            related_id: Second story identifier
            relation_type: Type of relation ("related" or "blocks")
        """
        story_id = ticket_id.lstrip("SC-").lstrip("#")
        related_story_id = related_id.lstrip("SC-").lstrip("#")

        # Map relation types to Shortcut verbs
        verb = "relates to" if relation_type == "related" else "blocks"

        try:
            self._request(
                "POST",
                f"/stories/{story_id}/story-links",
                json={
                    "object_id": int(related_story_id),
                    "verb": verb,
                },
            )
        except requests.HTTPError as e:
            raise RuntimeError(f"Failed to create relation: {e}") from e

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate Shortcut configuration."""
        issues = []

        if not self._api_token:
            issues.append("SHORTCUT_API_TOKEN not set")

        if self._api_token and not self.authenticate():
            issues.append("SHORTCUT_API_TOKEN is invalid or expired")

        return len(issues) == 0, issues

    def _get_label_ids(self, label_names: list[str]) -> list[int]:
        """Resolve label names to Shortcut label IDs."""
        if not label_names:
            return []
        label_names = self._normalize_labels(label_names)
        try:
            response = self._request("GET", "/labels")
            all_labels = response.json()
            name_to_id = {label["name"].lower(): label["id"] for label in all_labels}
            return [name_to_id[name.lower()] for name in label_names if name.lower() in name_to_id]
        except requests.RequestException:
            return []

    def _get_or_create_label_ids(self, label_names: list[str]) -> list[int]:
        """Resolve label names to IDs, creating any that don't exist."""
        if not label_names:
            return []
        try:
            response = self._request("GET", "/labels")
            all_labels = response.json()
            name_to_id = {label["name"].lower(): label["id"] for label in all_labels}

            label_ids = []
            for name in label_names:
                if name.lower() in name_to_id:
                    label_ids.append(name_to_id[name.lower()])
                else:
                    new_id = self._create_label(name)
                    if new_id:
                        label_ids.append(new_id)
            return label_ids
        except requests.RequestException:
            return self._get_label_ids(label_names)

    def _create_label(self, name: str) -> int | None:
        """Create a label in Shortcut and return its ID."""
        try:
            response = self._request("POST", "/labels", json={"name": name})
            label = response.json()
            label_id = label.get("id")
            return int(label_id) if label_id is not None else None
        except requests.RequestException:
            return None

    def list_labels(self) -> list[dict[str, Any]]:
        """List all labels with their IDs."""
        try:
            response = self._request("GET", "/labels")
            labels = response.json()
            return [
                {
                    "id": str(label.get("id", "")),
                    "name": label.get("name", ""),
                    "color": label.get("color", ""),
                }
                for label in labels
            ]
        except requests.RequestException:
            return []

    def _get_workflow_state_id(self, state_name: str) -> int | None:
        """Resolve workflow state name to state ID."""
        try:
            response = self._request("GET", "/workflows")
            workflows = response.json()
            # Search all workflows for matching state
            for workflow in workflows:
                for state in workflow.get("states", []):
                    if state.get("name", "").lower() == state_name.lower():
                        state_id = state.get("id")
                        return int(state_id) if state_id is not None else None
            return None
        except requests.RequestException:
            return None

    def _parse_story(self, story: dict) -> Ticket:
        """Parse a Shortcut story into a Ticket."""
        story_id = story.get("id", "")
        return Ticket(
            id=f"SC-{story_id}" if story_id else "",
            title=story.get("name", ""),
            description=story.get("description", ""),
            status=story.get("workflow_state", {}).get("name", ""),
            labels=[label.get("name", "") for label in story.get("labels", [])],
            url=story.get("app_url", ""),
            raw=story,
        )
