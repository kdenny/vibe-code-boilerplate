"""Base class for secret providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Secret:
    """Represents a secret from a provider."""

    name: str
    value: str | None  # None if we can't read the value
    environment: str
    provider: str


class SecretProvider(ABC):
    """Abstract base class for secret providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the provider name."""
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticate with the provider."""
        pass

    @abstractmethod
    def list_secrets(self, environment: str | None = None) -> list[Secret]:
        """List secrets, optionally filtered by environment."""
        pass

    @abstractmethod
    def get_secret(self, name: str, environment: str) -> Secret | None:
        """Get a specific secret."""
        pass

    @abstractmethod
    def set_secret(self, name: str, value: str, environment: str) -> bool:
        """Set a secret value."""
        pass

    @abstractmethod
    def delete_secret(self, name: str, environment: str) -> bool:
        """Delete a secret."""
        pass

    @abstractmethod
    def sync_from_local(self, env_file: str, environment: str) -> dict[str, bool]:
        """Sync secrets from a local env file to the provider."""
        pass
