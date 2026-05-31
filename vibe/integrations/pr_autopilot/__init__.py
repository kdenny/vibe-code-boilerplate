"""Reference PR Autopilot integration skeleton."""

from __future__ import annotations

from dataclasses import dataclass

from vibe.cli import Integration, verb
from vibe.errors import IntegrationError
from vibe.integrations.pr_autopilot.prototype import (
    configure_pr_autopilot,
    disable_pr_autopilot,
    enable_pr_autopilot,
    format_pr_autopilot_status,
    inspect_pr_autopilot,
)
from vibe.integrations.pr_autopilot.telemetry import (
    DEFAULT_TELEMETRY_LOG_PATH,
    CompositeTelemetrySink,
    JsonlTelemetrySink,
    LinearTelemetrySink,
    PRAutopilotRunTelemetry,
    PRAutopilotTelemetryEvent,
    format_linear_telemetry_comment,
    run_with_pr_autopilot_telemetry,
)


@dataclass(frozen=True)
class PRAutopilotConfig:
    """Typed config surface for the future PR Autopilot engine."""

    github_owner: str
    github_repo: str
    linear_team: str
    anthropic_api_key_ref: str | None = None


def _engine_not_installed() -> None:
    raise IntegrationError("PR Autopilot engine is not installed")


integration = Integration(
    name="pr_autopilot",
    config_cls=PRAutopilotConfig,
    verbs=(
        verb(
            "configure",
            handler=configure_pr_autopilot,
            help="Configure the prototype PR Autopilot integration",
            requires_extra=False,
        ),
        verb(
            "enable",
            handler=enable_pr_autopilot,
            help="Enable the prototype PR Autopilot integration",
            requires_extra=False,
        ),
        verb(
            "disable",
            handler=disable_pr_autopilot,
            help="Disable the prototype PR Autopilot integration",
            requires_extra=False,
        ),
        verb("run", handler=_engine_not_installed, help="Run the PR Autopilot loop"),
        verb(
            "status",
            handler=format_pr_autopilot_status,
            help="Show PR Autopilot prototype status",
            requires_extra=False,
        ),
        verb(
            "inspect",
            handler=inspect_pr_autopilot,
            help="Inspect the reviewable PR Autopilot artifacts",
            requires_extra=False,
        ),
    ),
    extra="pr-autopilot",
    extra_module="vibe_pr_autopilot",
    check=_engine_not_installed,
    description="Package seam for the PR Autopilot engine.",
    entrypoints={
        "configure": configure_pr_autopilot,
        "enable": enable_pr_autopilot,
        "disable": disable_pr_autopilot,
        "run": _engine_not_installed,
        "status": format_pr_autopilot_status,
        "inspect": inspect_pr_autopilot,
    },
)

__all__ = [
    "DEFAULT_TELEMETRY_LOG_PATH",
    "CompositeTelemetrySink",
    "JsonlTelemetrySink",
    "LinearTelemetrySink",
    "PRAutopilotConfig",
    "PRAutopilotRunTelemetry",
    "PRAutopilotTelemetryEvent",
    "format_linear_telemetry_comment",
    "integration",
    "run_with_pr_autopilot_telemetry",
]
