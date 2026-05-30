"""Tests for built-in integration skeletons."""

from dataclasses import is_dataclass
from pathlib import Path
import tomllib

import pytest

from lib.vibe.errors import MissingExtraError
from lib.vibe.integrations.pr_autopilot import PRAutopilotConfig, integration


def test_pr_autopilot_declares_reference_shape() -> None:
    assert integration.name == "pr_autopilot"
    assert integration.cli_name == "pr-autopilot"
    assert integration.config_cls is PRAutopilotConfig
    assert is_dataclass(PRAutopilotConfig)
    assert {verb.name for verb in integration.verbs} == {"run", "status"}
    assert integration.entrypoints.keys() == {"run", "status"}


def test_pr_autopilot_is_gated_by_extra() -> None:
    with pytest.raises(MissingExtraError) as exc_info:
        integration.ensure_extra_available()

    assert "vibe[pr-autopilot]" in str(exc_info.value)


def test_pr_autopilot_extra_and_entry_point_are_wired() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert "pr-autopilot" in pyproject["project"]["optional-dependencies"]
    assert (
        pyproject["project"]["entry-points"]["vibe.integrations"]["pr-autopilot"]
        == "lib.vibe.integrations.pr_autopilot:integration"
    )
