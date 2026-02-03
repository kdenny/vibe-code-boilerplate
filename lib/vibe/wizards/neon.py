"""Neon serverless Postgres setup wizard."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import click

from lib.vibe.tools import require_interactive


def check_neon_cli() -> bool:
    """Check if Neon CLI is installed."""
    return shutil.which("neonctl") is not None


def check_neon_auth() -> bool:
    """Check if Neon CLI is authenticated."""
    try:
        result = subprocess.run(
            ["neonctl", "me"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_env_vars() -> dict[str, bool]:
    """Check which Neon env vars are set."""
    vars_to_check = [
        "DATABASE_URL",
        "NEON_API_KEY",
        "NEON_PROJECT_ID",
    ]
    return {var: bool(os.environ.get(var)) for var in vars_to_check}


def run_neon_wizard(config: dict[str, Any]) -> bool:
    """
    Configure Neon integration.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    # Check prerequisites
    ok, error = require_interactive("Neon")
    if not ok:
        click.echo(f"\n{error}")
        return False

    click.echo("\n--- Neon Configuration ---")
    click.echo()

    # Step 1: Check CLI installation
    click.echo("Step 1: Checking Neon CLI...")
    if not check_neon_cli():
        click.echo("  Neon CLI (neonctl) is not installed.")
        click.echo("  Install with:")
        click.echo("    npm: npm install -g neonctl")
        click.echo("    macOS: brew install neonctl")
        if not click.confirm("  Continue after installing manually?", default=False):
            return False
        if not check_neon_cli():
            click.echo("  Neon CLI still not found. Please install and try again.")
            return False
    click.echo("  ✓ Neon CLI is installed")

    # Step 2: Check authentication
    click.echo("\nStep 2: Checking authentication...")
    if not check_neon_auth():
        click.echo("  Not authenticated with Neon.")
        if click.confirm("  Run 'neonctl auth' now?", default=True):
            click.echo("  Opening browser for authentication...")
            result = subprocess.run(["neonctl", "auth"])
            if result.returncode != 0:
                click.echo("  Authentication failed. Run 'neonctl auth' manually.")
                return False
            click.echo("  ✓ Authenticated")
        else:
            click.echo("  Authentication recommended. Run: neonctl auth")
    else:
        click.echo("  ✓ Authenticated with Neon")

    # Step 3: Project selection/creation
    click.echo("\nStep 3: Project setup...")
    project_id = os.environ.get("NEON_PROJECT_ID")

    if not project_id:
        click.echo("  No NEON_PROJECT_ID set.")
        choice = click.prompt(
            "  Create new project or use existing?",
            type=click.Choice(["new", "existing"]),
            default="existing",
        )

        if choice == "new":
            project_name = click.prompt("  Project name", default="my-app")
            click.echo(f"  Creating project '{project_name}'...")
            result = subprocess.run(
                ["neonctl", "projects", "create", "--name", project_name],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                click.echo("  ✓ Project created")
                click.echo("  Note: Copy the DATABASE_URL from the output to .env.local")
            else:
                click.echo(f"  Failed to create project: {result.stderr}")
                return False
        else:
            click.echo("  List projects with: neonctl projects list")
            click.echo("  Set NEON_PROJECT_ID in .env.local to your project ID")

    # Step 4: Check environment variables
    click.echo("\nStep 4: Checking environment variables...")
    env_vars = check_env_vars()
    env_local = Path(".env.local")

    has_db_url = env_vars.get("DATABASE_URL")

    if not has_db_url:
        click.echo("  DATABASE_URL not found.")
        click.echo("  Get connection string from:")
        click.echo("    • Neon dashboard: console.neon.tech > Connection Details")
        click.echo("    • CLI: neonctl connection-string")
        click.echo()
        click.echo("  Add to .env.local:")
        click.echo("    DATABASE_URL=postgres://user:pass@host/db")

        if not env_local.exists():
            if click.confirm("  Create .env.local template?", default=True):
                template = """# Neon Database Configuration
# Get connection string from: https://console.neon.tech

# Primary connection string (pooled, for serverless)
DATABASE_URL=

# Direct connection (for migrations)
# DIRECT_URL=

# Optional: for branch management
# NEON_API_KEY=
# NEON_PROJECT_ID=
"""
                env_local.write_text(template)
                click.echo("  ✓ Created .env.local template")
    else:
        click.echo("  ✓ DATABASE_URL configured")

    # Step 5: Database branching info
    click.echo("\nStep 5: Database branching...")
    click.echo("  Neon supports instant database branching for feature development.")
    click.echo("  Create a branch per feature/PR for isolated testing:")
    click.echo("    neonctl branches create --name feature-xyz")
    click.echo()
    click.echo("  See recipes/integrations/neon.md for CI/CD preview branch automation.")

    # Step 6: Update config
    click.echo("\nStep 6: Updating configuration...")

    # Ensure database config exists
    if "database" not in config:
        config["database"] = {}

    config["database"]["neon"] = {
        "enabled": True,
    }

    # Also set as primary database provider if not already set
    if not config["database"].get("provider"):
        config["database"]["provider"] = "neon"

    click.echo("  ✓ Configuration updated")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("  Neon Configuration Complete!")
    click.echo("=" * 50)
    click.echo()
    click.echo("Your project is configured for Neon serverless Postgres.")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Add DATABASE_URL to .env.local")
    click.echo("  2. For branching: neonctl branches create --name <branch>")
    click.echo("  3. For migrations: use your ORM's migration tool")
    click.echo()
    click.echo("Documentation: recipes/integrations/neon.md")
    click.echo()

    return True
