"""Supabase setup wizard."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import click


def check_supabase_cli() -> bool:
    """Check if Supabase CLI is installed."""
    return shutil.which("supabase") is not None


def check_supabase_auth() -> bool:
    """Check if Supabase CLI is authenticated."""
    try:
        result = subprocess.run(
            ["supabase", "projects", "list"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_supabase_init() -> bool:
    """Check if Supabase is initialized in this project."""
    return Path("supabase/config.toml").exists()


def check_supabase_linked() -> bool:
    """Check if project is linked to a Supabase project."""
    # Check for .supabase directory with project ref
    supabase_dir = Path(".supabase")
    if supabase_dir.exists():
        # Look for project ref file
        for f in supabase_dir.iterdir():
            if f.name.startswith("project"):
                return True
    return False


def check_env_vars() -> dict[str, bool]:
    """Check which Supabase env vars are set."""
    vars_to_check = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "NEXT_PUBLIC_SUPABASE_URL",
        "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    ]
    return {var: bool(os.environ.get(var)) for var in vars_to_check}


def run_supabase_wizard(config: dict[str, Any]) -> bool:
    """
    Configure Supabase integration.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    click.echo("\n--- Supabase Configuration ---")
    click.echo()

    # Step 1: Check CLI installation
    click.echo("Step 1: Checking Supabase CLI...")
    if not check_supabase_cli():
        click.echo("  Supabase CLI is not installed.")
        click.echo("  Install with:")
        click.echo("    macOS: brew install supabase/tap/supabase")
        click.echo("    npm: npm install -g supabase")
        if not click.confirm("  Continue after installing manually?", default=False):
            return False
        if not check_supabase_cli():
            click.echo("  Supabase CLI still not found. Please install and try again.")
            return False
    click.echo("  ✓ Supabase CLI is installed")

    # Step 2: Check authentication
    click.echo("\nStep 2: Checking authentication...")
    if not check_supabase_auth():
        click.echo("  Not authenticated with Supabase.")
        if click.confirm("  Run 'supabase login' now?", default=True):
            click.echo("  Opening browser for authentication...")
            result = subprocess.run(["supabase", "login"])
            if result.returncode != 0:
                click.echo("  Authentication failed. Run 'supabase login' manually.")
                return False
            click.echo("  ✓ Authenticated")
        else:
            click.echo("  Authentication recommended. Run: supabase login")
    else:
        click.echo("  ✓ Authenticated with Supabase")

    # Step 3: Check initialization
    click.echo("\nStep 3: Checking project initialization...")
    if not check_supabase_init():
        click.echo("  Project not initialized for Supabase.")
        if click.confirm("  Run 'supabase init' now?", default=True):
            result = subprocess.run(["supabase", "init"])
            if result.returncode != 0:
                click.echo("  Initialization failed. Run 'supabase init' manually.")
                return False
            click.echo("  ✓ Project initialized")
        else:
            click.echo("  Initialize when ready with: supabase init")
    else:
        click.echo("  ✓ Project initialized (supabase/config.toml exists)")

    # Step 4: Check project linking
    click.echo("\nStep 4: Checking project link...")
    if not check_supabase_linked():
        click.echo("  Project not linked to a Supabase project.")
        if click.confirm("  Link to an existing project now?", default=True):
            click.echo("  Run: supabase link --project-ref <your-project-ref>")
            project_ref = click.prompt("  Enter project ref (from Supabase dashboard)", default="")
            if project_ref:
                result = subprocess.run(["supabase", "link", "--project-ref", project_ref])
                if result.returncode == 0:
                    click.echo("  ✓ Project linked")
                else:
                    click.echo("  Linking failed. Link manually when ready.")
            else:
                click.echo("  Skipping link. Link later with: supabase link --project-ref <ref>")
        else:
            click.echo("  Link when ready with: supabase link --project-ref <ref>")
    else:
        click.echo("  ✓ Project linked to Supabase")

    # Step 5: Check environment variables
    click.echo("\nStep 5: Checking environment variables...")
    env_vars = check_env_vars()
    env_local = Path(".env.local")

    has_url = env_vars.get("SUPABASE_URL") or env_vars.get("NEXT_PUBLIC_SUPABASE_URL")
    has_key = env_vars.get("SUPABASE_ANON_KEY") or env_vars.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

    if not has_url or not has_key:
        click.echo("  Required environment variables not found.")
        click.echo("  Add these to .env.local:")
        click.echo("    SUPABASE_URL=https://your-project.supabase.co")
        click.echo("    SUPABASE_ANON_KEY=eyJ...")
        click.echo("    SUPABASE_SERVICE_ROLE_KEY=eyJ... (for server-side)")
        click.echo()
        click.echo("  Get these from: Supabase Dashboard > Project Settings > API")

        if not env_local.exists():
            if click.confirm("  Create .env.local template?", default=True):
                template = """# Supabase Configuration
# Get these values from: https://app.supabase.com > Project Settings > API

SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# For Next.js (client-side)
# NEXT_PUBLIC_SUPABASE_URL=
# NEXT_PUBLIC_SUPABASE_ANON_KEY=
"""
                env_local.write_text(template)
                click.echo("  ✓ Created .env.local template")
    else:
        click.echo("  ✓ Environment variables configured")

    # Step 6: Update config
    click.echo("\nStep 6: Updating configuration...")

    # Ensure database config exists
    if "database" not in config:
        config["database"] = {}

    config["database"]["supabase"] = {
        "enabled": True,
    }

    click.echo("  ✓ Configuration updated")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("  Supabase Configuration Complete!")
    click.echo("=" * 50)
    click.echo()
    click.echo("Your project is configured for Supabase.")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Add environment variables to .env.local")
    click.echo("  2. Start local dev: supabase start")
    click.echo("  3. Create migrations: supabase migration new <name>")
    click.echo("  4. Generate types: supabase gen types typescript --local")
    click.echo()
    click.echo("Documentation: recipes/databases/supabase.md")
    click.echo()

    return True
