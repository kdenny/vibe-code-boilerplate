"""Tests for the Axiom setup wizard."""

from unittest.mock import patch

from vibe.ui.validation import ValidationResult
from vibe.wizards.axiom import run_axiom_wizard


def test_records_config_and_runs_connectivity_when_env_present() -> None:
    config: dict = {}
    with (
        patch("vibe.wizards.axiom.require_interactive", return_value=(True, "")),
        patch(
            "vibe.wizards.axiom.check_env_vars",
            return_value={"AXIOM_API_TOKEN": True, "AXIOM_ORG_ID": True},
        ),
        patch("vibe.wizards.axiom.click.prompt", return_value="myapp-logs"),
        patch("vibe.wizards.axiom.click.echo"),
        patch("vibe.wizards.axiom.SetupValidator") as mock_validator_cls,
    ):
        mock_validator_cls.return_value.validate_axiom.return_value = ValidationResult(
            "Axiom", True, "Connected to dataset 'myapp-logs'", optional=True
        )
        result = run_axiom_wizard(config)

    assert result is True
    assert config["observability"]["axiom"] == {
        "enabled": True,
        "dataset": "myapp-logs",
    }
    # Connectivity check ran because env vars were present.
    mock_validator_cls.return_value.validate_axiom.assert_called_once()


def test_records_config_but_skips_connectivity_when_env_missing() -> None:
    config: dict = {}
    with (
        patch("vibe.wizards.axiom.require_interactive", return_value=(True, "")),
        patch(
            "vibe.wizards.axiom.check_env_vars",
            return_value={"AXIOM_API_TOKEN": False, "AXIOM_ORG_ID": False},
        ),
        patch("vibe.wizards.axiom.click.prompt", return_value="app-logs"),
        patch("vibe.wizards.axiom.click.confirm", return_value=False),
        patch("vibe.wizards.axiom.click.echo"),
        patch("vibe.wizards.axiom.SetupValidator") as mock_validator_cls,
    ):
        result = run_axiom_wizard(config)

    assert result is True
    assert config["observability"]["axiom"]["enabled"] is True
    # No connectivity check without credentials.
    mock_validator_cls.return_value.validate_axiom.assert_not_called()


def test_aborts_when_non_interactive() -> None:
    config: dict = {}
    with (
        patch(
            "vibe.wizards.axiom.require_interactive",
            return_value=(False, "needs a terminal"),
        ),
        patch("vibe.wizards.axiom.click.echo") as mock_echo,
    ):
        result = run_axiom_wizard(config)
    assert result is False
    assert "observability" not in config
    mock_echo.assert_called()
