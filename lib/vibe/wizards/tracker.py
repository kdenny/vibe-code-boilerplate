"""Ticket tracker selection wizard."""

import os
from typing import Any

import click


def run_tracker_wizard(config: dict[str, Any]) -> bool:
    """
    Configure ticket tracker integration.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    click.echo("Select your ticket tracking system:")
    click.echo()
    click.echo("  1. Linear - Full integration")
    click.echo("  2. Shortcut - Coming soon (stub)")
    click.echo("  3. None - Skip ticket tracking")
    click.echo()

    choice = click.prompt("Select option", type=int, default=1)

    if choice == 1:
        return _setup_linear(config)
    elif choice == 2:
        return _setup_shortcut(config)
    elif choice == 3:
        config["tracker"]["type"] = None
        click.echo("Ticket tracking disabled.")
        return True
    else:
        click.echo("Invalid choice")
        return False


def _setup_linear(config: dict[str, Any]) -> bool:
    """Set up Linear integration."""
    click.echo("\n--- Linear Setup ---")
    click.echo()
    click.echo("To get your Linear API key:")
    click.echo("  1. Go to Linear Settings > API")
    click.echo("  2. Create a new Personal API Key")
    click.echo("  3. Add to .env.local: LINEAR_API_KEY=lin_api_xxxxx")
    click.echo()

    # Check if already configured
    if os.environ.get("LINEAR_API_KEY"):
        click.echo("LINEAR_API_KEY detected in environment!")
    else:
        click.echo("Note: Add LINEAR_API_KEY to .env.local before using.")

    # Configure team
    click.echo()
    team_id = click.prompt(
        "Linear Team ID (optional, press Enter to skip)",
        default="",
        show_default=False,
    )

    workspace = click.prompt(
        "Linear Workspace slug (optional)",
        default="",
        show_default=False,
    )

    config["tracker"]["type"] = "linear"
    config["tracker"]["config"] = {
        "team_id": team_id if team_id else None,
        "workspace": workspace if workspace else None,
    }

    click.echo("\nLinear configured successfully!")

    # Prompt to enable native GitHub integration
    click.echo()
    click.echo("+" + "-" * 58 + "+")
    click.echo("|  Enable Linear's GitHub Integration (Recommended)        |")
    click.echo("+" + "-" * 58 + "+")
    click.echo("|                                                          |")
    click.echo("|  Linear's native integration automatically:              |")
    click.echo("|  - Links PRs to tickets based on branch names            |")
    click.echo("|  - Shows PR status in Linear                             |")
    click.echo("|  - Moves tickets to Done when PRs are merged             |")
    click.echo("|                                                          |")
    click.echo("|  Setup: Linear Settings > Integrations > GitHub          |")
    click.echo("|  Guide: recipes/tickets/linear-github-integration.md     |")
    click.echo("|                                                          |")
    click.echo("+" + "-" * 58 + "+")
    click.echo()

    if click.confirm("Open Linear GitHub integration docs now?", default=True):
        click.echo()
        click.echo("To enable the integration:")
        click.echo("  1. Go to: https://linear.app/settings/integrations/github")
        click.echo("  2. Click 'Connect GitHub'")
        click.echo("  3. Authorize Linear to access your repos")
        click.echo("  4. Enable auto-close on merge (recommended)")
        click.echo()
        click.echo("See recipes/tickets/linear-github-integration.md for full guide.")

    return True


def _setup_shortcut(config: dict[str, Any]) -> bool:
    """Set up Shortcut integration (stub)."""
    click.echo("\n--- Shortcut Setup ---")
    click.echo()
    click.echo("⚠️  Shortcut integration is not yet implemented.")
    click.echo("See GitHub issue #1 for tracking.")
    click.echo()
    click.echo("For now, you can:")
    click.echo("  1. Use Linear instead")
    click.echo("  2. Skip ticket tracking and add manually")
    click.echo()

    if click.confirm("Configure as placeholder (will not work yet)?", default=False):
        config["tracker"]["type"] = "shortcut"
        config["tracker"]["config"] = {
            "api_token": None,
            "workspace": None,
            "_stub": True,
        }
        click.echo("\nShortcut configured as placeholder.")
        return True

    return False
