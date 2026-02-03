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
            timeout=30,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_neon_projects() -> list[dict]:
    """Get list of Neon projects."""
    try:
        result = subprocess.run(
            ["neonctl", "projects", "list", "--output", "json"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            import json

            return json.loads(result.stdout)
        return []
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return []


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

    # Step 3: Check/select project
    click.echo("\nStep 3: Checking project configuration...")

    project_id = os.environ.get("NEON_PROJECT_ID")

    if not project_id:
        # Try to get current project context
        try:
            result = subprocess.run(
                ["neonctl", "projects", "list", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                import json

                projects = json.loads(result.stdout)
                if projects:
                    click.echo(f"  Found {len(projects)} Neon project(s)")

                    if len(projects) == 1:
                        project = projects[0]
                        project_id = project.get("id")
                        click.echo(f"  Using project: {project.get('name')} ({project_id})")
                    else:
                        click.echo("  Available projects:")
                        for i, p in enumerate(projects, 1):
                            click.echo(f"    {i}. {p.get('name')} ({p.get('id')})")

                        choice = click.prompt(
                            "  Select project number",
                            type=int,
                            default=1,
                        )
                        if 1 <= choice <= len(projects):
                            project = projects[choice - 1]
                            project_id = project.get("id")
                            click.echo(f"  Selected: {project.get('name')}")
                else:
                    click.echo("  No projects found.")
                    click.echo("  Create one at: https://console.neon.tech")
        except (subprocess.TimeoutExpired, Exception) as e:
            click.echo(f"  Could not list projects: {e}")

    # Step 4: Get connection string
    click.echo("\nStep 4: Getting connection string...")

    connection_string = None
    if project_id:
        try:
            result = subprocess.run(
                ["neonctl", "connection-string", "--project-id", project_id],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                connection_string = result.stdout.strip()
                # Mask password for display
                masked = connection_string
                if "@" in masked:
                    parts = masked.split("@")
                    user_pass = parts[0].split(":")
                    if len(user_pass) > 1:
                        masked = f"{user_pass[0]}:****@{parts[1]}"
                click.echo(f"  Connection string: {masked}")
        except (subprocess.TimeoutExpired, Exception) as e:
            click.echo(f"  Could not get connection string: {e}")

    if not connection_string:
        click.echo("  Get your connection string from: https://console.neon.tech")
        click.echo("  Dashboard > Your Project > Connection Details")

    # Step 5: Check environment variables
    click.echo("\nStep 5: Checking environment variables...")
    env_vars = check_env_vars()
    env_local = Path(".env.local")

    if not env_vars.get("DATABASE_URL"):
        click.echo("  DATABASE_URL not found.")

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
                if connection_string:
                    template = template.replace(
                        "DATABASE_URL=\n", f"DATABASE_URL={connection_string}\n"
                    )

                env_local.write_text(template)
                click.echo("  ✓ Created .env.local template")

                if connection_string:
                    click.echo("  ✓ Added connection string to .env.local")
        else:
            click.echo("  Add to .env.local:")
            if connection_string:
                click.echo(f"    DATABASE_URL={connection_string}")
            else:
                click.echo("    DATABASE_URL=postgres://user:pass@ep-xxx.aws.neon.tech/neondb")
    else:
        click.echo("  ✓ DATABASE_URL configured")

    # Check optional vars
    if not env_vars.get("NEON_API_KEY"):
        click.echo("  Note: NEON_API_KEY not set (needed for database branching)")

    # Step 6: Database branching info
    click.echo("\nStep 6: Database branching...")
    click.echo("  Neon supports instant database branching for feature development.")
    click.echo("  Create a branch per feature/PR for isolated testing:")
    click.echo("    neonctl branches create --name feature-xyz")
    click.echo()
    click.echo("  This works great with git worktrees - one DB branch per feature!")

    # Step 7: Update config
    click.echo("\nStep 7: Updating configuration...")

    # Ensure database config exists
    if "database" not in config:
        config["database"] = {}

    config["database"]["neon"] = {
        "enabled": True,
        "project_id": project_id,
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
    click.echo("  1. Ensure DATABASE_URL is in .env.local")
    click.echo("  2. For branching: neonctl branches create --name <branch>")
    click.echo("  3. For migrations: use your ORM's migration tool")
    click.echo()
    click.echo("For pooled connections (recommended for serverless):")
    click.echo("  Add ?pgbouncer=true to your DATABASE_URL")
    click.echo()
    click.echo("Documentation: recipes/databases/neon.md")
    click.echo()

    return True
