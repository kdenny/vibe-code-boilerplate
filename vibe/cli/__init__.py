"""CLI modules and public registry API for vibe commands."""

from vibe.cli.registry import (
    Integration,
    IntegrationRegistry,
    IntegrationVerb,
    get_registry,
    load_entry_point_integrations,
    register,
    verb,
)

__all__ = [
    "Integration",
    "IntegrationRegistry",
    "IntegrationVerb",
    "get_registry",
    "load_entry_point_integrations",
    "register",
    "verb",
]
