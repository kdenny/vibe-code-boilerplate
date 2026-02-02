"""Ticket CLI commands."""

import sys

import click

from lib.vibe.config import load_config
from lib.vibe.trackers.base import Ticket
from lib.vibe.trackers.linear import LinearTracker
from lib.vibe.trackers.shortcut import ShortcutTracker


def get_tracker():
    """Get the configured tracker instance."""
    config = load_config()
    tracker_type = config.get("tracker", {}).get("type")
    tracker_config = config.get("tracker", {}).get("config", {})

    if tracker_type == "linear":
        return LinearTracker(team_id=tracker_config.get("team_id"))
    elif tracker_type == "shortcut":
        return ShortcutTracker()
    else:
        return None


@click.group()
def main() -> None:
    """Ticket management commands."""
    pass


@main.command()
@click.argument("ticket_id")
def get(ticket_id: str) -> None:
    """Get details for a specific ticket."""
    tracker = get_tracker()
    if not tracker:
        click.echo("No tracker configured. Run 'bin/vibe setup'.", err=True)
        sys.exit(1)

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
    tracker = get_tracker()
    if not tracker:
        click.echo("No tracker configured. Run 'bin/vibe setup'.", err=True)
        sys.exit(1)

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
    tracker = get_tracker()
    if not tracker:
        click.echo("No tracker configured. Run 'bin/vibe setup'.", err=True)
        sys.exit(1)

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
