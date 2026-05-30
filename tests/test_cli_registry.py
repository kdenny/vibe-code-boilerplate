"""Tests for the integration CLI registry seam."""

from __future__ import annotations

from dataclasses import dataclass

import click
import pytest
from click.testing import CliRunner

from lib.vibe.cli import Integration, IntegrationRegistry, load_entry_point_integrations, verb
from lib.vibe.cli import registry as registry_module
from lib.vibe.cli.main import register_integration_commands


@dataclass(frozen=True)
class SampleConfig:
    value: str = "ok"


def test_registers_integration_verbs_as_cli_groups() -> None:
    root = click.Group()
    integration = Integration(
        name="sample_tool",
        config_cls=SampleConfig,
        verbs=(verb("ping", handler=lambda: "pong", help="Ping the sample integration"),),
        description="Sample integration.",
    )

    register_integration_commands(root, [integration])

    result = CliRunner().invoke(root, ["sample-tool", "ping"])

    assert result.exit_code == 0
    assert result.output.strip() == "pong"


def test_missing_extra_is_actionable_cli_error() -> None:
    root = click.Group()
    integration = Integration(
        name="pr_autopilot",
        config_cls=SampleConfig,
        verbs=(verb("run", handler=lambda: "should not run"),),
        extra="pr-autopilot",
        extra_module="definitely_missing_vibe_pr_autopilot_extra",
    )
    register_integration_commands(root, [integration])

    result = CliRunner().invoke(root, ["pr-autopilot", "run"])

    assert result.exit_code == 1
    assert "integration 'pr-autopilot' requires its extra" in result.output
    assert "uv pip install 'vibe[pr-autopilot]'" in result.output
    assert "Traceback" not in result.output


def test_registry_rejects_core_verb_shadowing() -> None:
    registry = IntegrationRegistry()
    integration = Integration(
        name="status",
        config_cls=SampleConfig,
        verbs=(verb("run", handler=lambda: None),),
    )

    with pytest.raises(ValueError, match="shadows core CLI verb"):
        registry.register(integration)


def test_loads_entry_point_integrations(monkeypatch: pytest.MonkeyPatch) -> None:
    registry = IntegrationRegistry()
    integration = Integration(
        name="sample",
        config_cls=SampleConfig,
        verbs=(verb("run", handler=lambda: None),),
    )

    class FakeEntryPoint:
        name = "sample"

        def load(self) -> Integration:
            return integration

    monkeypatch.setattr(
        registry_module,
        "_select_entry_points",
        lambda group: (FakeEntryPoint(),),
    )

    loaded = load_entry_point_integrations(registry=registry)

    assert loaded == (integration,)
    assert registry.get("sample") is integration


def test_bootstrap_survives_broken_entry_point(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from lib.vibe.cli import main as main_module

    def explode() -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(main_module, "load_entry_point_integrations", explode)
    monkeypatch.setattr(main_module, "register_integration_commands", lambda root: None)

    # A broken integration entry point must be reported, not propagated.
    main_module._bootstrap_integrations()

    assert "skipping a broken integration entry point" in capsys.readouterr().err
