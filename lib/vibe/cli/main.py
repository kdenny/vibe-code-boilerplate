"""Main CLI entry point for vibe commands."""

import sys

import click

from lib.vibe.doctor import print_results, run_doctor
from lib.vibe.wizards.setup import run_individual_wizard, run_setup


@click.group()
@click.version_option(version="0.1.0", prog_name="vibe")
def main() -> None:
    """Vibe Code Boilerplate - AI-assisted development workflows."""
    pass


@main.command()
@click.option("--force", "-f", is_flag=True, help="Force reconfiguration")
@click.option("--wizard", "-w", help="Run a specific wizard (github, tracker, branch, env)")
def setup(force: bool, wizard: str | None) -> None:
    """Run the setup wizard to configure your project."""
    if wizard:
        success = run_individual_wizard(wizard)
    else:
        success = run_setup(force=force)

    sys.exit(0 if success else 1)


@main.command()
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def doctor(verbose: bool) -> None:
    """Check project health and configuration."""
    results = run_doctor(verbose=verbose)
    sys.exit(print_results(results))


@main.command()
@click.argument("ticket_id")
def do(ticket_id: str) -> None:
    """Start working on a ticket (creates worktree and branch)."""
    from lib.vibe.config import load_config
    from lib.vibe.git.branches import format_branch_name
    from lib.vibe.git.worktrees import create_worktree
    from lib.vibe.trackers.linear import LinearTracker

    config = load_config()
    tracker_type = config.get("tracker", {}).get("type")

    # Get ticket info if tracker configured
    title = None
    if tracker_type == "linear":
        tracker = LinearTracker()
        ticket = tracker.get_ticket(ticket_id)
        if ticket:
            title = ticket.title
            click.echo(f"Found ticket: {ticket.title}")

    # Create branch name
    branch_name = format_branch_name(ticket_id, title)
    click.echo(f"Branch: {branch_name}")

    # Create worktree
    try:
        worktree = create_worktree(branch_name)
        click.echo(f"Worktree created at: {worktree.path}")
        click.echo(f"\nTo start working:\n  cd {worktree.path}")
    except Exception as e:
        click.echo(f"Failed to create worktree: {e}", err=True)
        sys.exit(1)


@main.command()
def pr() -> None:
    """Prepare and open a pull request."""
    click.echo("PR command not yet implemented.")
    click.echo("For now, use: gh pr create")
    sys.exit(1)


@main.group()
def secrets() -> None:
    """Manage secrets and environment variables."""
    pass


@secrets.command("list")
@click.option("--provider", "-p", help="Filter by provider (github, vercel, fly)")
def secrets_list(provider: str | None) -> None:
    """List configured secrets."""
    from lib.vibe.config import load_config

    config = load_config()
    providers = config.get("secrets", {}).get("providers", [])

    if not providers:
        click.echo("No secret providers configured.")
        click.echo("Run 'bin/vibe setup' to configure providers.")
        return

    click.echo(f"Configured providers: {', '.join(providers)}")

    if provider and provider not in providers:
        click.echo(f"Provider '{provider}' not configured.")
        return

    # TODO: Implement listing from each provider
    click.echo("\nSecret listing not yet fully implemented.")


@secrets.command("sync")
@click.argument("env_file", default=".env.local")
@click.option("--provider", "-p", required=True, help="Target provider")
@click.option("--environment", "-e", default="repository", help="Target environment")
def secrets_sync(env_file: str, provider: str, environment: str) -> None:
    """Sync secrets from a local env file to a provider."""
    click.echo(f"Syncing {env_file} to {provider}/{environment}...")
    click.echo("Secret syncing not yet fully implemented.")


if __name__ == "__main__":
    main()
