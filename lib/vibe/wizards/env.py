"""Environment and secrets configuration wizard."""

from typing import Any

import click


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
    click.echo("Secret Scanner Options:")
    click.echo("  1. Gitleaks (default) - Fast, widely used")
    click.echo("  2. TruffleHog - More comprehensive")
    click.echo("  3. None - Disable secret scanning")
    click.echo()

    scanner_choice = click.prompt("Select secret scanner", type=int, default=1)
    scanner_map = {1: "gitleaks", 2: "trufflehog", 3: None}
    secret_scanner = scanner_map.get(scanner_choice, "gitleaks")

    # SBOM generator
    click.echo("\nSBOM (Software Bill of Materials) Options:")
    click.echo("  1. Syft (default) - Comprehensive SBOM generation")
    click.echo("  2. GitHub Dependency Graph only")
    click.echo("  3. None - Disable SBOM generation")
    click.echo()

    sbom_choice = click.prompt("Select SBOM approach", type=int, default=1)
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
