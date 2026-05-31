"""Axiom log-shipping setup wizard.

Axiom is the optional observability lane for the pilot: it backs the ``bin/logs``
CLI and the ``/logs`` skill. This wizard configures the three env vars the CLI
reads (``AXIOM_API_TOKEN``, ``AXIOM_ORG_ID``, ``AXIOM_DATASET``), runs a live
connectivity check, and records ``observability.axiom`` in the project config so
``SetupValidator`` knows to validate it. Axiom is never required — Linear remains
the required failure-visibility path (see ``vibe/ui/validation.py``).
"""

import os
from pathlib import Path
from typing import Any

import click

from vibe.tools import require_interactive
from vibe.ui.validation import SetupValidator

# Env vars the bin/logs CLI reads (see recipes/observability/axiom.md).
REQUIRED_ENV_VARS = ("AXIOM_API_TOKEN", "AXIOM_ORG_ID")
DEFAULT_DATASET = "app-logs"


def check_env_vars() -> dict[str, bool]:
    """Check which Axiom env vars are set."""
    names = (*REQUIRED_ENV_VARS, "AXIOM_DATASET")
    return {name: bool(os.environ.get(name)) for name in names}


def run_axiom_wizard(config: dict[str, Any]) -> bool:
    """Configure the optional Axiom log integration.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was recorded
    """
    ok, error = require_interactive("Axiom")
    if not ok:
        click.echo(f"\n{error}")
        return False

    click.echo("\n--- Axiom Log Configuration (optional) ---")
    click.echo()
    click.echo(
        "Axiom backs the bin/logs CLI and the /logs skill. It is optional —\n"
        "Linear telemetry remains the required failure-visibility path."
    )

    # Step 1: Check environment variables
    click.echo("\nStep 1: Checking environment variables...")
    env_vars = check_env_vars()
    missing = [name for name in REQUIRED_ENV_VARS if not env_vars.get(name)]

    if missing:
        click.echo(f"  Missing: {', '.join(missing)}")
        click.echo("  Create a token at: app.axiom.co > Settings > API Tokens")
        click.echo("    (scope: Ingest + Query). Org ID: Settings > General.")
        click.echo()
        env_local = Path(".env.local")
        if not env_local.exists() and click.confirm("  Create .env.local template?", default=True):
            env_local.write_text(
                "# Axiom log shipping (see recipes/observability/axiom.md)\n"
                "AXIOM_API_TOKEN=xapt-\n"
                "AXIOM_ORG_ID=\n"
                "AXIOM_DATASET=app-logs\n"
            )
            click.echo("  ✓ Created .env.local template")
        click.echo("  Add the values, then re-run: bin/vibe setup -w axiom")
    else:
        click.echo("  ✓ AXIOM_API_TOKEN and AXIOM_ORG_ID set")

    # Step 2: Choose dataset
    click.echo("\nStep 2: Dataset...")
    default_dataset = os.environ.get("AXIOM_DATASET") or DEFAULT_DATASET
    dataset = click.prompt("  Dataset name", default=default_dataset).strip()

    # Step 3: Record config (so SetupValidator validates Axiom going forward).
    click.echo("\nStep 3: Updating configuration...")
    config.setdefault("observability", {})
    config["observability"]["axiom"] = {"enabled": True, "dataset": dataset}
    click.echo("  ✓ observability.axiom recorded")

    # Step 4: Live connectivity check (only meaningful once env vars exist).
    click.echo("\nStep 4: Connectivity check...")
    if missing:
        click.echo("  Skipped — set the env vars above first, then re-run.")
    else:
        result = SetupValidator(config).validate_axiom()
        marker = "✓" if result.success else "✗"
        click.echo(f"  {marker} {result.message}")
        if not result.success and result.details:
            click.echo(f"    {result.details}")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("  Axiom Configuration Recorded")
    click.echo("=" * 50)
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Ensure AXIOM_API_TOKEN / AXIOM_ORG_ID are in .env.local")
    click.echo("  2. Verify with: bin/logs health")
    click.echo("  3. Ship structured logs from your backend (see recipe)")
    click.echo()
    click.echo("Documentation: recipes/observability/axiom.md")
    click.echo()

    return True
