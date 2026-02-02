"""Abstract base class for ticket trackers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Ticket:
    """Represents a ticket from any tracker."""

    id: str
    title: str
    description: str
    status: str
    labels: list[str]
    url: str
    raw: dict[str, Any]


class TrackerBase(ABC):
    """Abstract base class for ticket tracker integrations."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the tracker name."""
        pass

    @abstractmethod
    def authenticate(self, **kwargs: Any) -> bool:
        """Authenticate with the tracker API."""
        pass

    @abstractmethod
    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Fetch a single ticket by ID."""
        pass

    @abstractmethod
    def list_tickets(
        self,
        status: str | None = None,
        labels: list[str] | None = None,
        limit: int = 50,
    ) -> list[Ticket]:
        """List tickets with optional filters."""
        pass

    @abstractmethod
    def create_ticket(
        self,
        title: str,
        description: str,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Create a new ticket."""
        pass

    @abstractmethod
    def update_ticket(
        self,
        ticket_id: str,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        labels: list[str] | None = None,
    ) -> Ticket:
        """Update an existing ticket."""
        pass

    def comment_ticket(self, ticket_id: str, body: str) -> None:
        """Add a comment to a ticket. Override in trackers that support comments."""
        raise NotImplementedError(
            f"Commenting is not supported by the {self.name} tracker."
        )

    @abstractmethod
    def validate_config(self) -> tuple[bool, list[str]]:
        """Validate tracker configuration. Returns (is_valid, list of issues)."""
        pass
