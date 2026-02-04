"""Environment and secrets configuration wizard."""

from typing import Any

import click

from lib.vibe.ui.components import NumberedMenu


def run_env_wizard(config: dict[str, Any]) -> bool:
    """
    Configure environment and secrets handling.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    click.echo("\n--- Environment & Secrets Configuration ---")
    click.echo()
    click.echo("This configures how secrets are managed across environments.")
    click.echo()

    # Secret scanner
    scanner_menu = NumberedMenu(
        title="Secret Scanner Options:",
        options=[
            ("Gitleaks", "Fast, widely used (Recommended)"),
            ("TruffleHog", "More comprehensive scanning"),
            ("None", "Disable secret scanning"),
        ],
        default=1,
    )

    scanner_choice = scanner_menu.show()
    scanner_map = {1: "gitleaks", 2: "trufflehog", 3: None}
    secret_scanner = scanner_map.get(scanner_choice, "gitleaks")

    # SBOM generator
    sbom_menu = NumberedMenu(
        title="\nSBOM (Software Bill of Materials) Options:",
        options=[
            ("Syft", "Comprehensive SBOM generation (Recommended)"),
            ("GitHub Dependency Graph", "Use GitHub's built-in feature"),
            ("None", "Disable SBOM generation"),
        ],
        default=1,
    )

    sbom_choice = sbom_menu.show()
    sbom_map = {1: "syft", 2: "github", 3: None}
    sbom_generator = sbom_map.get(sbom_choice, "syft")

    # Dependency scanning
    dep_scanning = click.confirm(
        "Enable dependency vulnerability scanning?",
        default=True,
    )

    # Secret providers
    click.echo("\nSecret Providers (where secrets are stored for deployment):")
    providers = []

    if click.confirm("Use GitHub Actions secrets?", default=True):
        providers.append("github")

    if click.confirm("Use Vercel environment variables?", default=False):
        providers.append("vercel")

    if click.confirm("Use Fly.io secrets?", default=False):
        providers.append("fly")

    # Update config
    config["security"] = {
        "secret_scanner": secret_scanner,
        "sbom_generator": sbom_generator,
        "dependency_scanning": dep_scanning,
    }

    config["secrets"] = {
        "providers": providers,
        "allowlist_path": ".vibe/secrets.allowlist.json",
    }

    click.echo("\nEnvironment configuration complete!")
    click.echo(f"  Secret scanner: {secret_scanner or 'disabled'}")
    click.echo(f"  SBOM generator: {sbom_generator or 'disabled'}")
    click.echo(f"  Secret providers: {', '.join(providers) if providers else 'none'}")

    return True
