"""Shortcut.com ticket tracker integration (stub)."""

from typing import Any

from lib.vibe.trackers.base import Ticket, TrackerBase


class ShortcutTracker(TrackerBase):
    """
    Shortcut.com integration.

    NOTE: This is a stub implementation. Full Shortcut integration is tracked
    in GitHub issue #1: https://github.com/YOUR_ORG/vibe-code-boilerplate/issues/1

    When implementing, reference:
    - Shortcut API docs: https://developer.shortcut.com/api/rest/v3
    - Similar patterns in linear.py
    """

    def __init__(self, api_token: str | None = None, workspace: str | None = None):
        self._api_token = api_token
        self._workspace = workspace

    @property
    def name(self) -> str:
        return "shortcut"

    def authenticate(self, **kwargs: Any) -> bool:
        """Authenticate with Shortcut API."""
        raise NotImplementedError(
            "Shortcut integration is not yet implemented. "
            "See GitHub issue #1 for tracking."
        )

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Fetch a single ticket by ID."""
        raise NotImplementedError(
            "Shortcut integration is not yet implemented. "
            "See GitHub issue #1 for tracking."
        )

    def list_tickets(
        self,
        status: str | None = None,
        labels: list[str] | None = None,
        limit: int = 50,
    ) -> list[Ticket]:
        """List tickets with optional filters."""
        raise NotImplementedError(
            "Shortcut integration is not yet implemented. "
            "See GitHub issue #1 for tracking."
        )

    def create_ticket(
        self,
        title: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Create a new ticket."""
        raise NotImplementedError(
            "Shortcut integration is not yet implemented. "
            "See GitHub issue #1 for tracking."
        )

    def update_ticket(
        self,
        ticket_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Update an existing ticket."""
        raise NotImplementedError(
            "Shortcut integration is not yet implemented. "
            "See GitHub issue #1 for tracking."
        )

    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate Shortcut configuration."""
        return False, [
            "Shortcut integration is not yet implemented. "
            "See GitHub issue #1 for tracking."
        ]
