"""Playwright E2E testing setup wizard."""

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import click

from lib.vibe.tools import require_interactive


def check_node() -> bool:
    """Check if Node.js is installed."""
    return shutil.which("node") is not None


def check_npm() -> bool:
    """Check if npm is installed."""
    return shutil.which("npm") is not None


def check_playwright_installed() -> bool:
    """Check if Playwright is installed in node_modules."""
    return Path("node_modules/@playwright/test").exists()


def check_playwright_config() -> Path | None:
    """Check if Playwright config exists and return the path."""
    for config_name in ["playwright.config.ts", "playwright.config.js", "playwright.config.mjs"]:
        config_path = Path(config_name)
        if config_path.exists():
            return config_path
    return None


def check_browsers_installed() -> bool:
    """Check if Playwright browsers are installed."""
    try:
        result = subprocess.run(
            ["npx", "playwright", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def detect_test_directory() -> Path | None:
    """Detect existing test directory."""
    candidates = [
        Path("tests"),
        Path("e2e"),
        Path("playwright"),
        Path("test"),
        Path("__tests__"),
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            # Check if it has any test files
            test_files = list(candidate.glob("**/*.spec.ts")) + list(candidate.glob("**/*.test.ts"))
            if test_files:
                return candidate
    return None


def detect_base_url() -> str | None:
    """Try to detect base URL from existing config or package.json."""
    # Check for Next.js
    if Path("next.config.js").exists() or Path("next.config.mjs").exists():
        return "http://localhost:3000"

    # Check package.json for dev script port
    package_json = Path("package.json")
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text())
            scripts = data.get("scripts", {})
            dev_script = scripts.get("dev", "")
            if "3000" in dev_script:
                return "http://localhost:3000"
            if "5173" in dev_script:  # Vite default
                return "http://localhost:5173"
            if "4321" in dev_script:  # Astro default
                return "http://localhost:4321"
        except (json.JSONDecodeError, KeyError):
            pass

    return None


def analyze_existing_config(config_path: Path) -> dict[str, Any]:
    """Analyze existing Playwright config for improvements."""
    analysis = {
        "has_base_url": False,
        "has_ci_config": False,
        "has_retries": False,
        "has_reporter": False,
        "browsers": [],
    }

    try:
        content = config_path.read_text()

        # Simple checks (not full parsing)
        analysis["has_base_url"] = "baseURL" in content
        analysis["has_ci_config"] = "CI" in content or "process.env.CI" in content
        analysis["has_retries"] = "retries" in content
        analysis["has_reporter"] = "reporter" in content

        # Check browsers
        if "chromium" in content.lower():
            analysis["browsers"].append("chromium")
        if "firefox" in content.lower():
            analysis["browsers"].append("firefox")
        if "webkit" in content.lower():
            analysis["browsers"].append("webkit")

    except Exception:
        pass

    return analysis


def run_playwright_wizard(config: dict[str, Any]) -> bool:
    """
    Configure Playwright E2E testing.

    Supports both new projects and retrofitting existing setups.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    # Check prerequisites
    ok, error = require_interactive("Playwright")
    if not ok:
        click.echo(f"\n{error}")
        return False

    click.echo("\n" + "=" * 50)
    click.echo("  Playwright E2E Testing Setup")
    click.echo("=" * 50)
    click.echo()

    # Step 1: Check Node.js
    click.echo("Step 1: Checking prerequisites...")
    if not check_node():
        click.echo("  ✗ Node.js is not installed")
        click.echo("  Install from: https://nodejs.org/")
        return False
    click.echo("  ✓ Node.js installed")

    if not check_npm():
        click.echo("  ✗ npm is not installed")
        return False
    click.echo("  ✓ npm installed")

    # Step 2: Check for existing Playwright setup
    click.echo("\nStep 2: Checking for existing Playwright setup...")
    existing_config = check_playwright_config()
    existing_tests = detect_test_directory()

    if existing_config:
        click.echo(f"  ✓ Found existing config: {existing_config}")
        is_retrofit = True

        # Analyze existing config
        analysis = analyze_existing_config(existing_config)
        click.echo()
        click.echo("  Current configuration:")
        click.echo(f"    Browsers: {', '.join(analysis['browsers']) or 'default'}")
        click.echo(f"    Base URL configured: {'Yes' if analysis['has_base_url'] else 'No'}")
        click.echo(f"    CI configuration: {'Yes' if analysis['has_ci_config'] else 'No'}")
        click.echo(f"    Retries configured: {'Yes' if analysis['has_retries'] else 'No'}")

        if existing_tests:
            test_count = len(list(existing_tests.glob("**/*.spec.ts"))) + len(
                list(existing_tests.glob("**/*.test.ts"))
            )
            click.echo(f"    Test files found: {test_count} in {existing_tests}/")

    else:
        click.echo("  No existing Playwright configuration found")
        is_retrofit = False

    # Step 3: Install or verify Playwright
    click.echo("\nStep 3: Playwright installation...")

    if not is_retrofit:
        # New project - initialize Playwright
        click.echo("  No Playwright setup detected.")
        if click.confirm("  Initialize Playwright now?", default=True):
            click.echo("\n  Running: npm init playwright@latest")
            click.echo("  (Follow the prompts to configure your setup)")
            click.echo()

            result = subprocess.run(["npm", "init", "playwright@latest"])

            if result.returncode != 0:
                click.echo("\n  Playwright initialization had issues.")
                click.echo("  You can run it manually: npm init playwright@latest")
            else:
                click.echo("\n  ✓ Playwright initialized")

            # Re-check config after init
            existing_config = check_playwright_config()

        else:
            click.echo("  Skipping initialization.")
            click.echo("  Run later with: npm init playwright@latest")

    else:
        # Existing project - check if packages installed
        if not check_playwright_installed():
            click.echo("  Playwright config exists but packages not installed.")
            if click.confirm("  Install Playwright packages?", default=True):
                click.echo("  Running: npm install -D @playwright/test")
                result = subprocess.run(["npm", "install", "-D", "@playwright/test"])
                if result.returncode == 0:
                    click.echo("  ✓ Playwright packages installed")
                else:
                    click.echo(
                        "  Installation failed. Run manually: npm install -D @playwright/test"
                    )
        else:
            click.echo("  ✓ Playwright packages installed")

    # Step 4: Install browsers
    click.echo("\nStep 4: Browser installation...")
    if click.confirm("  Install Playwright browsers? (Required for running tests)", default=True):
        click.echo("  Running: npx playwright install")
        result = subprocess.run(["npx", "playwright", "install"])
        if result.returncode == 0:
            click.echo("  ✓ Browsers installed")
        else:
            click.echo("  Browser installation had issues.")
            click.echo("  Run manually: npx playwright install")
    else:
        click.echo("  Skipping browser installation.")
        click.echo("  Install later with: npx playwright install")

    # Step 5: Configuration improvements (for retrofit)
    if is_retrofit and existing_config:
        click.echo("\nStep 5: Configuration review...")
        analysis = analyze_existing_config(existing_config)

        suggestions = []
        if not analysis["has_base_url"]:
            detected_url = detect_base_url()
            if detected_url:
                suggestions.append(f"Add baseURL: '{detected_url}' for cleaner test URLs")

        if not analysis["has_ci_config"]:
            suggestions.append("Add CI-specific config (retries, parallel workers)")

        if not analysis["has_retries"]:
            suggestions.append("Add retries: process.env.CI ? 2 : 0 for flaky test handling")

        if suggestions:
            click.echo("  Suggested improvements for your config:")
            for suggestion in suggestions:
                click.echo(f"    • {suggestion}")
            click.echo()
            click.echo("  See recipes/testing/playwright.md for configuration examples")
        else:
            click.echo("  ✓ Configuration looks good!")

    # Step 6: Update vibe config
    click.echo("\nStep 6: Updating configuration...")

    if "testing" not in config:
        config["testing"] = {}

    config["testing"]["playwright"] = {
        "enabled": True,
        "config_file": str(existing_config) if existing_config else "playwright.config.ts",
    }

    click.echo("  ✓ Configuration updated")

    # Summary
    click.echo("\n" + "=" * 50)
    click.echo("  Playwright Setup Complete!")
    click.echo("=" * 50)
    click.echo()

    if is_retrofit:
        click.echo("Your existing Playwright setup has been verified.")
    else:
        click.echo("Playwright has been initialized in your project.")

    click.echo()
    click.echo("Useful commands:")
    click.echo("  npx playwright test              # Run all tests")
    click.echo("  npx playwright test --ui         # Interactive UI mode")
    click.echo("  npx playwright codegen           # Generate tests by recording")
    click.echo("  npx playwright show-report       # View test report")
    click.echo("  npx playwright test --debug      # Debug mode")
    click.echo()
    click.echo("CI/CD:")
    click.echo("  Tests auto-run in GitHub Actions when playwright.config.ts exists")
    click.echo()
    click.echo("Documentation: recipes/testing/playwright.md")
    click.echo()

    return True
