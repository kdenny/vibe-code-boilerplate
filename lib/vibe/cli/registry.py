"""Integration registration seam for the Vibe CLI."""

from __future__ import annotations

import importlib.util
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from importlib import metadata
from typing import Any

from lib.vibe.errors import MissingExtraError

ENTRY_POINT_GROUP = "vibe.integrations"

CORE_VERBS = frozenset({"doctor", "status", "version"})


def _cli_slug(name: str) -> str:
    return name.replace("_", "-")


@dataclass(frozen=True)
class IntegrationVerb:
    """A CLI verb exposed by an integration."""

    name: str
    handler: Callable[..., Any]
    help: str = ""
    requires_extra: bool = True

    @property
    def cli_name(self) -> str:
        return _cli_slug(self.name)


@dataclass(frozen=True)
class Integration:
    """Declarative integration registration consumed by Vibe core."""

    name: str
    config_cls: type[Any]
    verbs: tuple[IntegrationVerb, ...]
    extra: str | None = None
    check: Callable[..., Any] | None = None
    extra_module: str | None = None
    description: str = ""
    entrypoints: dict[str, Callable[..., Any]] = field(default_factory=dict)

    @property
    def import_name(self) -> str:
        return self.name.replace("-", "_")

    @property
    def cli_name(self) -> str:
        return _cli_slug(self.name)

    def ensure_extra_available(self) -> None:
        """Raise a clear error if this integration's optional dependency is missing."""

        if not self.extra or not self.extra_module:
            return
        if importlib.util.find_spec(self.extra_module) is None:
            raise MissingExtraError(self.cli_name, self.extra)


def verb(
    name: str,
    handler: Callable[..., Any],
    help: str = "",
    *,
    requires_extra: bool = True,
) -> IntegrationVerb:
    """Declare one CLI verb for an integration."""

    return IntegrationVerb(
        name=name,
        handler=handler,
        help=help,
        requires_extra=requires_extra,
    )


class IntegrationRegistry:
    """In-memory registry of available integrations."""

    def __init__(self) -> None:
        self._integrations: dict[str, Integration] = {}

    def register(self, integration: Integration) -> Integration:
        """Register an integration and return it for decorator-style use."""

        if integration.cli_name in CORE_VERBS:
            raise ValueError(f"integration '{integration.name}' shadows core CLI verb")
        if integration.cli_name in self._integrations:
            raise ValueError(f"integration '{integration.name}' is already registered")
        self._integrations[integration.cli_name] = integration
        return integration

    def get(self, name: str) -> Integration | None:
        return self._integrations.get(_cli_slug(name))

    def all(self) -> tuple[Integration, ...]:
        return tuple(self._integrations[name] for name in sorted(self._integrations))


_REGISTRY = IntegrationRegistry()


def register(integration: Integration) -> Integration:
    """Register an integration with the process-global CLI registry."""

    return _REGISTRY.register(integration)


def get_registry() -> IntegrationRegistry:
    """Return the process-global integration registry."""

    return _REGISTRY


def load_entry_point_integrations(
    *,
    group: str = ENTRY_POINT_GROUP,
    registry: IntegrationRegistry | None = None,
) -> tuple[Integration, ...]:
    """Load integrations declared via package entry points."""

    target = registry or _REGISTRY
    loaded: list[Integration] = []
    for entry_point in _select_entry_points(group):
        integration = entry_point.load()
        if not isinstance(integration, Integration):
            raise TypeError(
                f"entry point {entry_point.name!r} returned {type(integration).__name__}, "
                "expected Integration"
            )
        loaded.append(target.register(integration))
    return tuple(loaded)


def _select_entry_points(group: str) -> Iterable[metadata.EntryPoint]:
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        return entry_points.select(group=group)
    return entry_points.get(group, ())  # type: ignore[union-attr]
