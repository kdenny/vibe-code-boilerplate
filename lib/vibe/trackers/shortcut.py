"""Shortcut.com ticket tracker integration."""

import os
from typing import Any

import requests

from lib.vibe.trackers.base import Ticket, TrackerBase

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
            response = requests.get(
                f"{SHORTCUT_API_URL}/member",
                headers=self._headers,
                timeout=30,
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Fetch a single story by ID."""
        # Shortcut story IDs are numeric
        story_id = ticket_id.lstrip("SC-").lstrip("#")
        try:
            response = requests.get(
                f"{SHORTCUT_API_URL}/stories/{story_id}",
                headers=self._headers,
                timeout=30,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            story = response.json()
            return self._parse_story(story)
        except Exception:
            return None

    def list_tickets(
        self,
        status: str | None = None,
        labels: list[str] | None = None,
        limit: int = 50,
    ) -> list[Ticket]:
        """List stories with optional filters using search."""
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

        try:
            response = requests.get(
                f"{SHORTCUT_API_URL}/search/stories",
                headers=self._headers,
                params={"query": search_query, "page_size": limit},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            stories = data.get("data", [])
            return [self._parse_story(story) for story in stories[:limit]]
        except Exception:
            return []

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
            response = requests.post(
                f"{SHORTCUT_API_URL}/stories",
                headers=self._headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
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
            response = requests.put(
                f"{SHORTCUT_API_URL}/stories/{story_id}",
                headers=self._headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            story = response.json()
            return self._parse_story(story)
        except requests.HTTPError as e:
            raise RuntimeError(f"Failed to update ticket: {e}") from e

    def comment_ticket(self, ticket_id: str, body: str) -> None:
        """Add a comment to a story."""
        story_id = ticket_id.lstrip("SC-").lstrip("#")
        try:
            response = requests.post(
                f"{SHORTCUT_API_URL}/stories/{story_id}/comments",
                headers=self._headers,
                json={"text": body},
                timeout=30,
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"Failed to add comment: {e}") from e

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
            response = requests.get(
                f"{SHORTCUT_API_URL}/labels",
                headers=self._headers,
                timeout=30,
            )
            response.raise_for_status()
            all_labels = response.json()
            name_to_id = {label["name"].lower(): label["id"] for label in all_labels}
            return [name_to_id[name.lower()] for name in label_names if name.lower() in name_to_id]
        except Exception:
            return []

    def _get_or_create_label_ids(self, label_names: list[str]) -> list[int]:
        """Resolve label names to IDs, creating any that don't exist."""
        if not label_names:
            return []
        try:
            response = requests.get(
                f"{SHORTCUT_API_URL}/labels",
                headers=self._headers,
                timeout=30,
            )
            response.raise_for_status()
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
        except Exception:
            return self._get_label_ids(label_names)

    def _create_label(self, name: str) -> int | None:
        """Create a label in Shortcut and return its ID."""
        try:
            response = requests.post(
                f"{SHORTCUT_API_URL}/labels",
                headers=self._headers,
                json={"name": name},
                timeout=30,
            )
            response.raise_for_status()
            label = response.json()
            return label.get("id")
        except Exception:
            return None

    def list_labels(self) -> list[dict[str, Any]]:
        """List all labels with their IDs."""
        try:
            response = requests.get(
                f"{SHORTCUT_API_URL}/labels",
                headers=self._headers,
                timeout=30,
            )
            response.raise_for_status()
            labels = response.json()
            return [
                {
                    "id": str(label.get("id", "")),
                    "name": label.get("name", ""),
                    "color": label.get("color", ""),
                }
                for label in labels
            ]
        except Exception:
            return []

    def _get_workflow_state_id(self, state_name: str) -> int | None:
        """Resolve workflow state name to state ID."""
        try:
            response = requests.get(
                f"{SHORTCUT_API_URL}/workflows",
                headers=self._headers,
                timeout=30,
            )
            response.raise_for_status()
            workflows = response.json()
            # Search all workflows for matching state
            for workflow in workflows:
                for state in workflow.get("states", []):
                    if state.get("name", "").lower() == state_name.lower():
                        return state.get("id")
            return None
        except Exception:
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
