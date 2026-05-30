"""Public error hierarchy for Vibe core and integrations."""

from __future__ import annotations


class VibeError(Exception):
    """Base class for catchable Vibe package errors."""


class ConfigError(VibeError):
    """Raised when config is missing or invalid."""


class MissingExtraError(VibeError):
    """Raised when an integration is used without its optional extra installed."""

    def __init__(self, integration: str, extra: str) -> None:
        self.integration = integration
        self.extra = extra
        super().__init__(
            f"integration '{integration}' requires its extra.\n"
            f"Install it with:  uv pip install 'vibe[{extra}]'"
        )


class SecretResolutionError(VibeError):
    """Raised when a secret reference cannot be resolved."""


class IntegrationError(VibeError):
    """Raised when an integration provider operation fails."""
