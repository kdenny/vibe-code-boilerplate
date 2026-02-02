"""Branch naming convention wizard."""

from typing import Any

import click


def run_branch_wizard(config: dict[str, Any]) -> bool:
    """
    Configure branch naming convention.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
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
    pattern = click.prompt("Branch pattern", default=current)

    # Main branch
    main_branch = click.prompt(
        "Main branch name",
        default=config.get("branching", {}).get("main_branch", "main"),
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
