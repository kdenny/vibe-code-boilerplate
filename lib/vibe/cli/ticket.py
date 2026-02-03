"""Ticket CLI commands."""

import os
import sys
from pathlib import Path

import click

from lib.vibe.config import load_config, save_config
from lib.vibe.deployment_followup import (
    build_human_followup_body,
    detect_deployment_platforms,
    get_default_human_followup_title,
)
from lib.vibe.trackers.base import Ticket
from lib.vibe.trackers.linear import LinearTracker
from lib.vibe.trackers.shortcut import ShortcutTracker
from lib.vibe.wizards.tracker import run_tracker_wizard


def get_tracker():
    """Get the configured tracker instance (config file or LINEAR_* env for CI)."""
    config = load_config()
    tracker_type = config.get("tracker", {}).get("type")
    tracker_config = config.get("tracker", {}).get("config", {})

    if tracker_type == "linear":
        return LinearTracker(team_id=tracker_config.get("team_id"))
    if tracker_type == "shortcut":
        return ShortcutTracker()
    # CI: allow Linear via env when no tracker is configured (e.g. HUMAN follow-up workflow)
    if os.environ.get("LINEAR_API_KEY"):
        return LinearTracker(
            team_id=tracker_config.get("team_id") or os.environ.get("LINEAR_TEAM_ID")
        )
    return None


def ensure_tracker_configured():
    """
    Return the configured tracker, or prompt to run the tracker setup wizard.
    Exits with a message if the user declines or setup does not configure a tracker.
    """
    tracker = get_tracker()
    if tracker is not None:
        return tracker

    click.echo(
        "No ticketing system (e.g. Linear) is configured. Set up a tracker before creating or viewing tickets."
    )
    if not click.confirm("Run tracker setup now?", default=True):
        click.echo(
            "Run 'bin/vibe setup' or 'bin/vibe setup --wizard tracker' when ready.", err=True
        )
        sys.exit(1)

    config = load_config()
    if not run_tracker_wizard(config):
        click.echo(
            "Tracker setup was cancelled or failed. Run 'bin/vibe setup' to try again.", err=True
        )
        sys.exit(1)
    save_config(config)

    tracker = get_tracker()
    if tracker is None:
        click.echo(
            "No tracker was selected. Run 'bin/vibe setup' to configure one later.", err=True
        )
        sys.exit(1)
    return tracker


@click.group()
def main() -> None:
    """Ticket management commands."""
    pass


@main.command()
@click.argument("ticket_id")
def get(ticket_id: str) -> None:
    """Get details for a specific ticket."""
    tracker = ensure_tracker_configured()

    try:
        ticket = tracker.get_ticket(ticket_id)
        if ticket:
            print_ticket(ticket)
        else:
            click.echo(f"Ticket not found: {ticket_id}")
            sys.exit(1)
    except NotImplementedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command("list")
@click.option("--status", "-s", help="Filter by status")
@click.option("--label", "-l", multiple=True, help="Filter by label")
@click.option("--limit", "-n", default=10, help="Maximum tickets to show")
def list_tickets(status: str | None, label: tuple, limit: int) -> None:
    """List tickets from the tracker."""
    tracker = ensure_tracker_configured()

    try:
        tickets = tracker.list_tickets(
            status=status,
            labels=list(label) if label else None,
            limit=limit,
        )

        if not tickets:
            click.echo("No tickets found.")
            return

        for ticket in tickets:
            print_ticket_summary(ticket)
    except NotImplementedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command()
@click.argument("title")
@click.option("--description", "-d", default="", help="Ticket description")
@click.option("--label", "-l", multiple=True, help="Labels to add")
def create(title: str, description: str, label: tuple) -> None:
    """Create a new ticket."""
    tracker = ensure_tracker_configured()

    try:
        ticket = tracker.create_ticket(
            title=title,
            description=description,
            labels=list(label) if label else None,
        )
        click.echo(f"Created ticket: {ticket.id}")
        click.echo(f"URL: {ticket.url}")
    except NotImplementedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


HUMAN_FOLLOWUP_LABELS = ["Chore", "Infra", "HUMAN"]


@main.command("create-human-followup")
@click.option(
    "--files",
    "-f",
    multiple=True,
    help="Changed file paths (e.g. from git diff). If not set, scan repo for deployment configs.",
)
@click.option("--parent", "-p", "parent_ticket_id", help="Parent ticket ID (e.g. PROJ-123)")
@click.option("--print-only", is_flag=True, help="Print ticket body only; do not create")
@click.option("--env-path", default=".env.example", help="Path to .env.example for instructions")
def create_human_followup(
    files: tuple,
    parent_ticket_id: str | None,
    print_only: bool,
    env_path: str,
) -> None:
    """Create a HUMAN-labeled follow-up ticket for deployment infrastructure setup.

    Use after completing a deployment infra ticket (fly.toml, vercel.json, .env.example).
    Detects platforms from changed files or repo scan and builds step-by-step instructions.
    """
    config = load_config()
    repo_owner = config.get("github", {}).get("owner", "")
    repo_name = config.get("github", {}).get("repo", "")
    if not repo_owner and not repo_name and os.environ.get("GITHUB_REPOSITORY"):
        parts = os.environ["GITHUB_REPOSITORY"].split("/", 1)
        repo_owner = parts[0] if len(parts) > 0 else ""
        repo_name = parts[1] if len(parts) > 1 else ""
    changed_files = list(files) if files else None
    repo_root = Path.cwd()

    platforms = detect_deployment_platforms(
        changed_files=changed_files,
        repo_root=repo_root,
    )
    if not platforms:
        click.echo(
            "No deployment configs detected. Add --files with paths like fly.toml, vercel.json, .env.example, "
            "or run from a repo that contains them.",
            err=True,
        )
        sys.exit(1)

    body = build_human_followup_body(
        platforms=platforms,
        repo_owner=repo_owner,
        repo_name=repo_name,
        parent_ticket_id=parent_ticket_id,
        env_example_path=env_path,
    )
    title = get_default_human_followup_title()

    if print_only:
        click.echo(f"Title: {title}")
        click.echo(f"Labels: {', '.join(HUMAN_FOLLOWUP_LABELS)}")
        click.echo("\nDescription:\n")
        click.echo(body)
        return

    tracker = ensure_tracker_configured()
    try:
        ticket = tracker.create_ticket(
            title=title,
            description=body,
            labels=HUMAN_FOLLOWUP_LABELS,
        )
        click.echo(f"Created HUMAN follow-up ticket: {ticket.id}")
        click.echo(f"URL: {ticket.url}")
    except NotImplementedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command()
@click.argument("ticket_id")
@click.option("--status", "-s", help="Set ticket status (e.g. Done, In Progress)")
@click.option("--title", "-t", help="Set ticket title")
@click.option("--description", "-d", help="Set ticket description")
@click.option(
    "--label",
    "-l",
    multiple=True,
    help="Set labels (replaces existing for trackers that support it)",
)
def update(
    ticket_id: str,
    status: str | None,
    title: str | None,
    description: str | None,
    label: tuple,
) -> None:
    """Update a ticket (status, title, description, labels)."""
    tracker = ensure_tracker_configured()

    if not any([status, title, description, label]):
        click.echo("Specify at least one of: --status, --title, --description, --label", err=True)
        sys.exit(1)

    try:
        ticket = tracker.update_ticket(
            ticket_id,
            title=title,
            description=description,
            status=status,
            labels=list(label) if label else None,
        )
        click.echo(f"Updated: {ticket.id}")
        click.echo(f"Status: {ticket.status}")
        click.echo(f"URL: {ticket.url}")
    except NotImplementedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command()
@click.argument("ticket_id")
@click.option("--cancel", is_flag=True, help="Mark as canceled instead of done")
def close(ticket_id: str, cancel: bool) -> None:
    """Close a ticket (set status to Done or Canceled)."""
    tracker = ensure_tracker_configured()

    status = "Canceled" if cancel else "Done"
    try:
        ticket = tracker.update_ticket(ticket_id, status=status)
        click.echo(f"Closed: {ticket.id} ({ticket.status})")
        click.echo(f"URL: {ticket.url}")
    except NotImplementedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command()
@click.argument("ticket_id")
@click.argument("message")
def comment(ticket_id: str, message: str) -> None:
    """Add a comment to a ticket."""
    tracker = ensure_tracker_configured()

    try:
        tracker.comment_ticket(ticket_id, message)
        click.echo(f"Comment added to {ticket_id}")
    except NotImplementedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


@main.command()
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def labels(as_json: bool) -> None:
    """List all labels with their IDs.

    Useful for API calls that require label IDs instead of names.
    """
    tracker = ensure_tracker_configured()

    if not hasattr(tracker, "list_labels"):
        click.echo("Label listing not supported for this tracker", err=True)
        sys.exit(1)

    try:
        label_list = tracker.list_labels()
        if not label_list:
            click.echo("No labels found.")
            return

        if as_json:
            import json

            click.echo(json.dumps(label_list, indent=2))
        else:
            click.echo("\nLabels:")
            click.echo("-" * 60)
            for label in sorted(label_list, key=lambda x: x.get("name", "")):
                name = label.get("name", "")
                label_id = label.get("id", "")
                color = label.get("color", "")
                click.echo(f"  {name:<30} {label_id}")
                if color:
                    click.echo(f"    Color: {color}")
            click.echo()
            click.echo("Tip: Use label IDs in API calls for reliability.")
    except NotImplementedError as e:
        click.echo(str(e), err=True)
        sys.exit(1)


def print_ticket(ticket: Ticket) -> None:
    """Print full ticket details."""
    click.echo(f"\n{ticket.id}: {ticket.title}")
    click.echo("-" * 60)
    click.echo(f"Status: {ticket.status}")
    click.echo(f"Labels: {', '.join(ticket.labels) if ticket.labels else 'none'}")
    click.echo(f"URL: {ticket.url}")
    if ticket.description:
        click.echo(f"\nDescription:\n{ticket.description}")
    click.echo()


def print_ticket_summary(ticket: Ticket) -> None:
    """Print ticket summary line."""
    labels = f" [{', '.join(ticket.labels)}]" if ticket.labels else ""
    click.echo(f"  {ticket.id}: {ticket.title} ({ticket.status}){labels}")


if __name__ == "__main__":
    main()
