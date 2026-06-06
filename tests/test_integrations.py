"""Tests for built-in integration skeletons."""

import tomllib
from dataclasses import is_dataclass
from pathlib import Path

import pytest

from vibe.errors import MissingExtraError
from vibe.integrations.pr_autopilot import PRAutopilotConfig, integration
from vibe.integrations.pr_autopilot.prototype import (
    ANTHROPIC_SECRET_NAME,
    ANTHROPIC_SECRET_REF,
    ToolResult,
    configure_pr_autopilot,
    disable_pr_autopilot,
    enable_pr_autopilot,
    format_pr_autopilot_status,
    inspect_pr_autopilot,
)


def test_pr_autopilot_declares_reference_shape() -> None:
    assert integration.name == "pr_autopilot"
    assert integration.cli_name == "pr-autopilot"
    assert integration.config_cls is PRAutopilotConfig
    assert is_dataclass(PRAutopilotConfig)
    assert {verb.name for verb in integration.verbs} == {
        "configure",
        "disable",
        "enable",
        "inspect",
        "run",
        "setup",
        "status",
    }
    assert integration.entrypoints.keys() == {
        "configure",
        "disable",
        "enable",
        "inspect",
        "run",
        "setup",
        "status",
    }


def test_pr_autopilot_is_gated_by_extra() -> None:
    with pytest.raises(MissingExtraError) as exc_info:
        integration.ensure_extra_available()

    assert "vibe[pr-autopilot]" in str(exc_info.value)


def test_pr_autopilot_extra_and_entry_point_are_wired() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text())

    assert "pr-autopilot" in pyproject["project"]["optional-dependencies"]
    assert (
        pyproject["project"]["entry-points"]["vibe.integrations"]["pr-autopilot"]
        == "vibe.integrations.pr_autopilot:integration"
    )


def test_configure_writes_layered_toml_without_secret_values(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = _fake_provider_runner(secret_present=False)

    output = configure_pr_autopilot(runner=runner)
    second_output = configure_pr_autopilot(runner=runner)

    core = tomllib.loads((tmp_path / ".vibe/config.toml").read_text())
    pr_config = tomllib.loads((tmp_path / ".vibe/pr-autopilot.toml").read_text())
    assert core["github"] == {"owner": "kevin-earl-denny", "repo": "demo"}
    assert pr_config["integration"]["enabled"] is True
    assert pr_config["secrets"]["anthropic_api_key"] == ANTHROPIC_SECRET_REF
    assert "sk-ant" not in (tmp_path / ".vibe/pr-autopilot.toml").read_text()
    assert "gh secret set" in output
    assert "none (already up to date)" in second_output


def test_status_reconciles_secret_drift(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = _fake_provider_runner(secret_present=False)
    configure_pr_autopilot(runner=runner)

    output = format_pr_autopilot_status(runner=runner)

    assert "configured: yes" in output
    assert "enabled: yes" in output
    assert f"secret {ANTHROPIC_SECRET_NAME}: missing" in output
    assert f"missing GitHub secret {ANTHROPIC_SECRET_NAME}" in output


def test_enable_disable_round_trips_presence_enablement(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    runner = _fake_provider_runner(secret_present=True)
    configure_pr_autopilot(runner=runner)

    disabled_output = disable_pr_autopilot()
    assert not (tmp_path / ".vibe/pr-autopilot.toml").exists()
    assert (tmp_path / ".vibe/pr-autopilot.toml.disabled").exists()
    assert "integration is off" in disabled_output

    enabled_output = enable_pr_autopilot(runner=runner)
    assert (tmp_path / ".vibe/pr-autopilot.toml").exists()
    assert not (tmp_path / ".vibe/pr-autopilot.toml.disabled").exists()
    assert "Restored" in enabled_output


def test_inspect_reports_reviewable_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    configure_pr_autopilot(runner=_fake_provider_runner(secret_present=True))

    output = inspect_pr_autopilot()

    assert "# .vibe/config.toml" in output
    assert "# .vibe/pr-autopilot.toml" in output
    assert ANTHROPIC_SECRET_REF in output
    assert "never values" in output


def _fake_provider_runner(*, secret_present: bool):
    def run(command: tuple[str, ...]) -> ToolResult:
        if command[:3] == ("gh", "repo", "view"):
            return ToolResult(
                command=command,
                returncode=0,
                stdout='{"owner": {"login": "kevin-earl-denny"}, "name": "demo"}',
            )
        if command[:3] == ("gh", "secret", "list"):
            secrets = [{"name": ANTHROPIC_SECRET_NAME}] if secret_present else []
            return ToolResult(command=command, returncode=0, stdout=str(secrets).replace("'", '"'))
        if command[:3] == ("gh", "auth", "status"):
            return ToolResult(command=command, returncode=0)
        raise AssertionError(f"unexpected provider command: {command}")

    return run
