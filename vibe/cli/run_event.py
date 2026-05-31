"""CLI for emitting PR Autopilot run telemetry.

The autopilot loop is driven by shell/Markdown today, not a long-lived Python
process, so this CLI is how the loop records a run's lifecycle:

    bin/vibe-run-event start --ticket VIBE-146 --pr <url> --engine claude
    bin/vibe-run-event complete --outcome success
    bin/vibe-run-event reconcile          # backstop: recover crashed runs

``start`` prints the run id and remembers it as the machine's current run, so
``complete`` needs no id in the common single-run-per-machine case.
"""

import json
import os

import click

# Auto-load .env files at startup (unless disabled), matching the other CLIs.
if os.environ.get("VIBE_NO_DOTENV") != "1":
    from vibe.env import auto_load_env

    auto_load_env(verbose=os.environ.get("VIBE_VERBOSE") == "1")

from vibe.events import Outcome, RunRecord, default_telemetry


def _record_summary(record: RunRecord) -> dict:
    """The fields worth printing for a run (the durable record, trimmed)."""
    return {
        "run_id": record.run_id,
        "state": record.state,
        "ticket": record.ticket,
        "pr_url": record.pr_url,
        "engine": record.engine,
        "outcome": record.outcome,
        "reason": record.reason,
        "started_at": record.started_at,
        "ended_at": record.ended_at,
    }


@click.group()
def main() -> None:
    """Emit start/completion telemetry for PR Autopilot runs."""


@main.command()
@click.option("--ticket", required=True, help="Ticket the run is for (e.g. VIBE-146).")
@click.option("--pr", "pr_url", default=None, help="PR URL, once one is open.")
@click.option("--engine", default=None, help="Coding engine driving the run (e.g. claude).")
@click.option("--run-id", default=None, help="Explicit run id (default: generated).")
@click.option(
    "--timeout-seconds",
    type=float,
    default=None,
    help="Declared ceiling; reconcile flags a run past it as a timeout.",
)
@click.option(
    "--no-current",
    is_flag=True,
    help="Do not record this run as the machine's current run.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit the record as JSON.")
def start(
    ticket: str,
    pr_url: str | None,
    engine: str | None,
    run_id: str | None,
    timeout_seconds: float | None,
    no_current: bool,
    as_json: bool,
) -> None:
    """Record the start of a run."""
    telemetry = default_telemetry()
    record = telemetry.start(
        ticket=ticket,
        pr_url=pr_url,
        engine=engine,
        run_id=run_id,
        timeout_seconds=timeout_seconds,
        set_current=not no_current,
    )
    if as_json:
        click.echo(json.dumps(_record_summary(record), indent=2))
    else:
        click.echo(record.run_id)


@main.command()
@click.option(
    "--outcome",
    required=True,
    type=click.Choice([o.value for o in Outcome]),
    help="How the run ended.",
)
@click.option("--run-id", default=None, help="Run to complete (default: current run).")
@click.option("--reason", default=None, help="Why it ended (shown on failures/timeouts).")
@click.option("--json", "as_json", is_flag=True, help="Emit the record as JSON.")
def complete(outcome: str, run_id: str | None, reason: str | None, as_json: bool) -> None:
    """Record the terminal outcome of a run (idempotent)."""
    telemetry = default_telemetry()
    try:
        record = telemetry.complete(outcome=Outcome(outcome), run_id=run_id, reason=reason)
    except (KeyError, ValueError) as exc:
        raise click.ClickException(str(exc)) from exc
    if as_json:
        click.echo(json.dumps(_record_summary(record), indent=2))
    else:
        click.echo(f"{record.run_id} {record.outcome}")


@main.command()
@click.option(
    "--deadline-seconds",
    type=float,
    default=None,
    help="Fallback ceiling for running records that declared no timeout.",
)
@click.option("--json", "as_json", is_flag=True, help="Emit repaired runs as JSON.")
def reconcile(deadline_seconds: float | None, as_json: bool) -> None:
    """Recover crashed/stuck runs by synthesizing their missing completion."""
    telemetry = default_telemetry()
    repaired = telemetry.reconcile(deadline_seconds=deadline_seconds)
    if as_json:
        click.echo(json.dumps([_record_summary(r) for r in repaired], indent=2))
        return
    if not repaired:
        click.echo("No stale runs to reconcile.")
        return
    for record in repaired:
        click.echo(f"{record.run_id} -> {record.outcome} ({record.reason})")


@main.command(name="list")
@click.option("--json", "as_json", is_flag=True, help="Emit records as JSON.")
def list_runs(as_json: bool) -> None:
    """List recorded runs, most recent first."""
    from vibe.events import store

    records = sorted(store.iter_records(), key=lambda r: r.started_at, reverse=True)
    if as_json:
        click.echo(json.dumps([_record_summary(r) for r in records], indent=2))
        return
    if not records:
        click.echo("No runs recorded.")
        return
    for record in records:
        outcome = record.outcome or "running"
        ticket = record.ticket or "-"
        click.echo(f"{record.run_id}  {ticket:<12}  {outcome}")


if __name__ == "__main__":
    from vibe.cli.errors import run_cli

    run_cli(main, "vibe.cli.run_event")
