"""Initial setup wizard orchestrator."""

import click

from lib.vibe.config import config_exists, load_config, save_config
from lib.vibe.wizards.branch import run_branch_wizard
from lib.vibe.wizards.env import run_env_wizard
from lib.vibe.wizards.github import run_github_wizard
from lib.vibe.wizards.tracker import run_tracker_wizard


def run_setup(force: bool = False) -> bool:
    """
    Run the initial setup wizard.

    Args:
        force: Force re-running setup even if config exists

    Returns:
        True if setup completed successfully
    """
    click.echo("=" * 60)
    click.echo("  Vibe Code Boilerplate - Setup Wizard")
    click.echo("=" * 60)
    click.echo()

    # Check for existing config
    if config_exists() and not force:
        click.echo("Configuration already exists at .vibe/config.json")
        if not click.confirm("Do you want to reconfigure?", default=False):
            click.echo("Setup cancelled. Use 'vibe setup --force' to reconfigure.")
            return False

    config = load_config()

    # Essential wizards (required)
    click.echo("\n--- Essential Configuration ---\n")

    # 1. GitHub auth
    click.echo("Step 1: GitHub Authentication")
    if not run_github_wizard(config):
        click.echo("GitHub authentication is required. Setup cancelled.")
        return False

    # 2. Tracker selection
    click.echo("\nStep 2: Ticket Tracker")
    if not run_tracker_wizard(config):
        click.echo("Tracker configuration is required. Setup cancelled.")
        return False

    # Save after essentials
    save_config(config)

    # Optional wizards
    click.echo("\n--- Optional Configuration ---\n")

    if click.confirm("Configure branch naming convention?", default=False):
        run_branch_wizard(config)
        save_config(config)

    if click.confirm("Configure environment/secrets handling?", default=False):
        run_env_wizard(config)
        save_config(config)

    # Final save and summary
    save_config(config)

    click.echo("\n" + "=" * 60)
    click.echo("  Setup Complete!")
    click.echo("=" * 60)
    click.echo()
    click.echo("Configuration saved to .vibe/config.json")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Run 'bin/doctor' to verify your setup")
    click.echo("  2. Review .vibe/config.json and adjust as needed")
    click.echo("  3. Check out the recipes/ directory for best practices")
    click.echo()

    return True


def run_individual_wizard(wizard_name: str) -> bool:
    """
    Run a specific wizard by name.

    Args:
        wizard_name: Name of wizard to run (github, tracker, branch, env)

    Returns:
        True if wizard completed successfully
    """
    config = load_config()

    wizards = {
        "github": run_github_wizard,
        "tracker": run_tracker_wizard,
        "branch": run_branch_wizard,
        "env": run_env_wizard,
    }

    if wizard_name not in wizards:
        click.echo(f"Unknown wizard: {wizard_name}")
        click.echo(f"Available wizards: {', '.join(wizards.keys())}")
        return False

    result = wizards[wizard_name](config)
    if result:
        save_config(config)

    return result
