"""Debug and verbose output utilities."""

import os
import sys
import traceback

import click


def is_verbose() -> bool:
    """Check if verbose/debug mode is enabled."""
    return os.environ.get("VIBE_DEBUG") == "1" or "--verbose" in sys.argv


def handle_unexpected_error(e: Exception, context: str = "") -> None:
    """Handle an unexpected error with optional verbose traceback."""
    if is_verbose():
        click.echo(traceback.format_exc(), err=True)
    prefix = f"{context}: " if context else ""
    click.echo(f"{prefix}Unexpected error: {e}", err=True)
    click.echo("Run with VIBE_DEBUG=1 for full traceback.", err=True)
