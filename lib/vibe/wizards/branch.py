"""Branch naming convention wizard."""

from typing import Any

import click

from lib.vibe.tools import (
    get_default_branch,
    require_interactive,
    validate_branch_pattern,
)


def run_branch_wizard(config: dict[str, Any]) -> bool:
    """
    Configure branch naming convention.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    # Check prerequisites
    ok, error = require_interactive("Branch")
    if not ok:
        click.echo(f"\n{error}")
        return False

    click.echo("\n--- Branch Naming Convention ---")
    click.echo()
    click.echo("Branch naming helps link branches to tickets automatically.")
    click.echo()
    click.echo("Available placeholders:")
    click.echo("  {PROJ} - Project prefix from ticket (e.g., PROJ)")
    click.echo("  {num}  - Ticket number (e.g., 123)")
    click.echo()
    click.echo("Examples:")
    click.echo("  {PROJ}-{num}        → PROJ-123")
    click.echo("  feature/{PROJ}-{num} → feature/PROJ-123")
    click.echo("  {PROJ}/{num}        → PROJ/123")
    click.echo()

    current = config.get("branching", {}).get("pattern", "{PROJ}-{num}")

    # Prompt with validation
    while True:
        pattern = click.prompt("Branch pattern", default=current)
        is_valid, error_msg = validate_branch_pattern(pattern)
        if is_valid:
            break
        click.echo(f"  Invalid: {error_msg}")

    # Main branch - detect from git if possible
    detected_main = get_default_branch()
    current_main = config.get("branching", {}).get("main_branch", detected_main)
    main_branch = click.prompt(
        "Main branch name",
        default=current_main,
    )

    # Rebase policy
    always_rebase = click.confirm(
        "Always rebase onto main before PR? (recommended)",
        default=config.get("branching", {}).get("always_rebase", True),
    )

    config["branching"] = {
        "pattern": pattern,
        "main_branch": main_branch,
        "always_rebase": always_rebase,
    }

    # Show example
    example_branch = pattern.replace("{PROJ}", "PROJ").replace("{num}", "123")
    click.echo(f"\nExample branch: {example_branch}")
    click.echo("Branch naming configured successfully!")

    return True
