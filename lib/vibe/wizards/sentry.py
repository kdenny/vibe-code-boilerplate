"""Sentry setup wizard."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

import click

from lib.vibe.tools import require_interactive
from lib.vibe.ui.components import NumberedMenu


def check_sentry_cli() -> bool:
    """Check if Sentry CLI is installed."""
    return shutil.which("sentry-cli") is not None


def check_sentry_auth() -> bool:
    """Check if Sentry CLI is authenticated."""
    try:
        result = subprocess.run(
            ["sentry-cli", "info"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0 and "Not logged in" not in result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_env_vars() -> dict[str, bool]:
    """Check which Sentry env vars are set."""
    vars_to_check = [
        "SENTRY_DSN",
        "SENTRY_AUTH_TOKEN",
        "SENTRY_ORG",
        "SENTRY_PROJECT",
    ]
    return {var: bool(os.environ.get(var)) for var in vars_to_check}


def detect_framework() -> str | None:
    """Detect the project framework for Sentry setup."""
    # Check for Next.js
    if Path("next.config.js").exists() or Path("next.config.mjs").exists():
        return "nextjs"

    # Check for Python
    if Path("requirements.txt").exists() or Path("pyproject.toml").exists():
        return "python"

    # Check for Node.js
    if Path("package.json").exists():
        return "node"

    return None


def check_sentry_configured() -> bool:
    """Check if Sentry is already configured in the project."""
    # Check for Next.js Sentry config
    if any(
        Path(f).exists()
        for f in [
            "sentry.client.config.ts",
            "sentry.client.config.js",
            "sentry.server.config.ts",
            "sentry.server.config.js",
        ]
    ):
        return True

    # Check for env var
    if os.environ.get("SENTRY_DSN"):
        return True

    return False


def run_sentry_wizard(config: dict[str, Any]) -> bool:
    """
    Configure Sentry integration.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    # Check prerequisites
    ok, error = require_interactive("Sentry")
    if not ok:
        click.echo(f"\n{error}")
        return False

    click.echo("\n--- Sentry Configuration ---")
    click.echo()

    # Step 1: Check CLI installation
    click.echo("Step 1: Checking Sentry CLI...")
    if not check_sentry_cli():
        click.echo("  Sentry CLI is not installed.")
        click.echo("  Install with:")
        click.echo("    macOS: brew install getsentry/tools/sentry-cli")
        click.echo("    npm: npm install -g @sentry/cli")
        if not click.confirm("  Continue after installing manually?", default=False):
            return False
        if not check_sentry_cli():
            click.echo("  Sentry CLI still not found. Please install and try again.")
            return False
    click.echo("  ✓ Sentry CLI is installed")

    # Step 2: Check authentication
    click.echo("\nStep 2: Checking authentication...")
    if not check_sentry_auth():
        click.echo("  Not authenticated with Sentry.")
        if click.confirm("  Run 'sentry-cli login' now?", default=True):
            click.echo("  Opening browser for authentication...")
            result = subprocess.run(["sentry-cli", "login"])
            if result.returncode != 0:
                click.echo("  Authentication failed. Run 'sentry-cli login' manually.")
                return False
            click.echo("  ✓ Authenticated")
        else:
            click.echo("  Authentication recommended. Run: sentry-cli login")
    else:
        click.echo("  ✓ Authenticated with Sentry")

    # Step 3: Detect framework
    click.echo("\nStep 3: Detecting framework...")
    framework = detect_framework()
    if framework:
        click.echo(f"  Detected framework: {framework}")
    else:
        click.echo("  Could not auto-detect framework")
        menu = NumberedMenu(
            title="  Select framework:",
            options=[
                ("Next.js", "React framework with SSR"),
                ("Python", "Django, Flask, FastAPI, etc."),
                ("Node.js", "Express, Fastify, etc."),
                ("Other", "See docs.sentry.io for setup"),
            ],
            default=4,
        )
        choice = menu.show()
        framework_map = {1: "nextjs", 2: "python", 3: "node", 4: "other"}
        framework = framework_map.get(choice, "other")

    # Step 4: Framework-specific setup
    click.echo(f"\nStep 4: Setting up Sentry for {framework}...")

    if framework == "nextjs":
        if check_sentry_configured():
            click.echo("  Sentry already configured (sentry.*.config.ts found)")
        else:
            if click.confirm("  Run Sentry wizard for Next.js?", default=True):
                click.echo("  Running: npx @sentry/wizard@latest -i nextjs")
                result = subprocess.run(["npx", "@sentry/wizard@latest", "-i", "nextjs"])
                if result.returncode == 0:
                    click.echo("  ✓ Sentry configured for Next.js")
                else:
                    click.echo("  Setup had issues. Check output above.")
            else:
                click.echo("  Skipping. Run manually: npx @sentry/wizard@latest -i nextjs")

    elif framework == "python":
        click.echo("  For Python, add to your app initialization:")
        click.echo()
        click.echo("    import sentry_sdk")
        click.echo()
        click.echo("    sentry_sdk.init(")
        click.echo('        dsn=os.environ["SENTRY_DSN"],')
        click.echo("        traces_sample_rate=0.1,")
        click.echo("    )")
        click.echo()
        click.echo("  Install: pip install sentry-sdk")

    elif framework == "node":
        click.echo("  For Node.js, add to your app initialization:")
        click.echo()
        click.echo('    const Sentry = require("@sentry/node");')
        click.echo()
        click.echo("    Sentry.init({")
        click.echo("      dsn: process.env.SENTRY_DSN,")
        click.echo("      tracesSampleRate: 0.1,")
        click.echo("    });")
        click.echo()
        click.echo("  Install: npm install @sentry/node")

    else:
        click.echo("  See https://docs.sentry.io for setup instructions")

    # Step 5: Check environment variables
    click.echo("\nStep 5: Checking environment variables...")
    env_vars = check_env_vars()
    env_local = Path(".env.local")

    if not env_vars.get("SENTRY_DSN"):
        click.echo("  SENTRY_DSN not found.")
        click.echo("  Get your DSN from: sentry.io > Project > Settings > Client Keys")
        click.echo()
        click.echo("  Add to .env.local:")
        click.echo("    SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx")

        if not env_local.exists():
            if click.confirm("  Create .env.local template?", default=True):
                template = """# Sentry Configuration
# Get DSN from: https://sentry.io > Project > Settings > Client Keys

SENTRY_DSN=

# For release tracking (optional)
# Get auth token from: https://sentry.io > Settings > Auth Tokens
SENTRY_AUTH_TOKEN=
SENTRY_ORG=
SENTRY_PROJECT=
"""
                env_local.write_text(template)
                click.echo("  ✓ Created .env.local template")
    else:
        click.echo("  ✓ SENTRY_DSN configured")

    # Check optional vars
    if not env_vars.get("SENTRY_AUTH_TOKEN"):
        click.echo("  Note: SENTRY_AUTH_TOKEN not set (needed for release tracking)")
    if not env_vars.get("SENTRY_ORG"):
        click.echo("  Note: SENTRY_ORG not set (needed for release tracking)")
    if not env_vars.get("SENTRY_PROJECT"):
        click.echo("  Note: SENTRY_PROJECT not set (needed for release tracking)")

    # Step 6: Update config
    click.echo("\nStep 6: Updating configuration...")

    # Ensure observability config exists
    if "observability" not in config:
        config["observability"] = {}

    config["observability"]["sentry"] = {
        "enabled": True,
        "framework": framework,
    }

    click.echo("  ✓ Configuration updated")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("  Sentry Configuration Complete!")
    click.echo("=" * 50)
    click.echo()
    click.echo("Your project is configured for Sentry error monitoring.")
    click.echo()
    click.echo("Next steps:")
    click.echo("  1. Add SENTRY_DSN to .env.local")
    click.echo("  2. Add SENTRY_AUTH_TOKEN, SENTRY_ORG, SENTRY_PROJECT for releases")
    click.echo("  3. Test with: sentry-cli send-event -m 'Test event'")
    click.echo("  4. Set up release tracking in CI (see recipe)")
    click.echo()
    click.echo("Documentation: recipes/integrations/sentry.md")
    click.echo()

    return True
