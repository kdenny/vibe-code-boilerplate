"""Vercel setup wizard."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import click


def check_vercel_cli() -> bool:
    """Check if Vercel CLI is installed."""
    return shutil.which("vercel") is not None


def check_vercel_auth() -> bool:
    """Check if Vercel CLI is authenticated."""
    try:
        result = subprocess.run(
            ["vercel", "whoami"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_vercel_user() -> str | None:
    """Get the authenticated Vercel user."""
    try:
        result = subprocess.run(
            ["vercel", "whoami"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None


def check_project_linked() -> bool:
    """Check if project is linked to Vercel."""
    vercel_dir = Path(".vercel")
    project_json = vercel_dir / "project.json"
    return project_json.exists()


def get_project_info() -> dict | None:
    """Get linked project info."""
    project_json = Path(".vercel/project.json")
    if project_json.exists():
        try:
            return json.loads(project_json.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return None


def run_vercel_wizard(config: dict[str, Any]) -> bool:
    """
    Configure Vercel deployment.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    click.echo("\n--- Vercel Deployment Configuration ---")
    click.echo()

    # Step 1: Check CLI installation
    click.echo("Step 1: Checking Vercel CLI...")
    if not check_vercel_cli():
        click.echo("  Vercel CLI is not installed.")
        if click.confirm("  Install Vercel CLI now?", default=True):
            click.echo("  Installing Vercel CLI...")
            result = subprocess.run(
                ["npm", "install", "-g", "vercel"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                click.echo(f"  Failed to install: {result.stderr}")
                click.echo("  Install manually: npm install -g vercel")
                return False
            click.echo("  ✓ Vercel CLI installed")
        else:
            click.echo("  Vercel CLI is required. Install with: npm install -g vercel")
            return False
    else:
        click.echo("  ✓ Vercel CLI is installed")

    # Step 2: Check authentication
    click.echo("\nStep 2: Checking authentication...")
    if not check_vercel_auth():
        click.echo("  Not authenticated with Vercel.")
        if click.confirm("  Run 'vercel login' now?", default=True):
            click.echo("  Opening browser for authentication...")
            result = subprocess.run(["vercel", "login"])
            if result.returncode != 0:
                click.echo("  Authentication failed. Run 'vercel login' manually.")
                return False
            click.echo("  ✓ Authenticated")
        else:
            click.echo("  Authentication required. Run: vercel login")
            return False
    else:
        user = get_vercel_user()
        click.echo(f"  ✓ Authenticated as {user}")

    # Step 3: Check project linking
    click.echo("\nStep 3: Checking project link...")
    if not check_project_linked():
        click.echo("  Project is not linked to Vercel.")
        if click.confirm("  Run 'vercel link' now?", default=True):
            click.echo("  Linking project...")
            result = subprocess.run(["vercel", "link"])
            if result.returncode != 0:
                click.echo("  Linking failed. Run 'vercel link' manually.")
                return False
            click.echo("  ✓ Project linked")
        else:
            click.echo("  Project linking is recommended. Run: vercel link")
    else:
        project_info = get_project_info()
        if project_info:
            org_id = project_info.get("orgId", "unknown")
            project_id = project_info.get("projectId", "unknown")
            click.echo(f"  ✓ Project linked (org: {org_id[:8]}..., project: {project_id[:8]}...)")

    # Step 4: Environment variables
    click.echo("\nStep 4: Environment variables...")
    env_local = Path(".env.local")
    if not env_local.exists():
        if click.confirm("  Pull environment variables from Vercel?", default=True):
            click.echo("  Pulling environment variables...")
            result = subprocess.run(
                ["vercel", "env", "pull", ".env.local"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                click.echo("  ✓ Environment variables pulled to .env.local")
            else:
                click.echo("  Could not pull env vars (project may not have any set)")
    else:
        click.echo("  ✓ .env.local already exists")

    # Step 5: Update config
    click.echo("\nStep 5: Updating configuration...")

    # Ensure deployment config exists
    if "deployment" not in config:
        config["deployment"] = {}

    config["deployment"]["vercel"] = {
        "enabled": True,
    }

    # Add to secrets providers if not already present
    if "secrets" not in config:
        config["secrets"] = {"providers": []}
    if "vercel" not in config["secrets"].get("providers", []):
        config["secrets"]["providers"] = config["secrets"].get("providers", []) + ["vercel"]

    click.echo("  ✓ Configuration updated")

    # Step 6: Create vercel.json if needed
    vercel_json = Path("vercel.json")
    if not vercel_json.exists():
        if click.confirm("\nCreate vercel.json with defaults?", default=False):
            default_config = {
                "buildCommand": "npm run build",
                "outputDirectory": "dist",
            }

            # Detect framework
            package_json = Path("package.json")
            if package_json.exists():
                try:
                    pkg = json.loads(package_json.read_text())
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "next" in deps:
                        default_config = {"framework": "nextjs"}
                    elif "vite" in deps:
                        default_config = {"framework": "vite", "outputDirectory": "dist"}
                    elif "remix" in deps:
                        default_config = {"framework": "remix"}
                except (json.JSONDecodeError, OSError):
                    pass

            vercel_json.write_text(json.dumps(default_config, indent=2) + "\n")
            click.echo("  ✓ Created vercel.json")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("  Vercel Configuration Complete!")
    click.echo("=" * 50)
    click.echo()
    click.echo("Your project is ready for Vercel deployment.")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Deploy preview: vercel")
    click.echo("  2. Deploy production: vercel --prod")
    click.echo("  3. Connect GitHub in Vercel dashboard for auto-deploys")
    click.echo()

    return True
