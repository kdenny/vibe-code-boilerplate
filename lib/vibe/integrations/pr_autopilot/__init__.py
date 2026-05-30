"""Reference PR Autopilot integration skeleton."""

from __future__ import annotations

from dataclasses import dataclass

from lib.vibe.cli import Integration, verb
from lib.vibe.errors import IntegrationError


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
        verb("run", handler=_engine_not_installed, help="Run the PR Autopilot loop"),
        verb("status", handler=_engine_not_installed, help="Show PR Autopilot status"),
    ),
    extra="pr-autopilot",
    extra_module="vibe_pr_autopilot",
    check=_engine_not_installed,
    description="Package seam for the PR Autopilot engine.",
    entrypoints={"run": _engine_not_installed, "status": _engine_not_installed},
)

__all__ = ["PRAutopilotConfig", "integration"]
