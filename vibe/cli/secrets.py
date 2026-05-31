"""Secrets CLI commands."""

import os
import sys

import click

# Auto-load .env files at startup (unless disabled)
if os.environ.get("VIBE_NO_DOTENV") != "1":
    from vibe.env import auto_load_env

    auto_load_env(verbose=os.environ.get("VIBE_VERBOSE") == "1")

from vibe.config import load_config
from vibe.secrets.allowlist import add_to_allowlist, load_allowlist


@click.group()
def main() -> None:
    """Secret management commands."""
    pass


@main.command("list")
@click.option("--provider", "-p", help="Filter by provider")
def list_secrets(provider: str | None) -> None:
    """List secrets from configured providers."""
    config = load_config()
    providers = config.get("secrets", {}).get("providers", [])

    if not providers:
        click.echo("No secret providers configured.")
        return

    if provider:
        if provider not in providers:
            click.echo(f"Provider '{provider}' not configured.")
            sys.exit(1)
        providers = [provider]

    for prov in providers:
        click.echo(f"\n{prov.upper()} Secrets:")
        click.echo("-" * 40)

        if prov == "github":
            from vibe.secrets.providers.github import GitHubSecretsProvider

            github_config = config.get("github", {})
            gh = GitHubSecretsProvider(
                owner=github_config.get("owner"),
                repo=github_config.get("repo"),
            )

            if not gh.authenticate():
                click.echo("  Not authenticated. Run 'gh auth login'.")
                continue

            secrets = gh.list_secrets()
            if secrets:
                for secret in secrets:
                    click.echo(f"  {secret.name} ({secret.environment})")
            else:
                click.echo("  No secrets found.")
        else:
            click.echo(f"  Provider '{prov}' not yet implemented.")


@main.group("allowlist")
def allowlist() -> None:
    """Manage the secrets allowlist."""
    pass


@allowlist.command("list")
def allowlist_list() -> None:
    """List allowlist entries."""
    entries = load_allowlist()

    if not entries:
        click.echo("No allowlist entries.")
        return

    click.echo("\nSecrets Allowlist:")
    click.echo("-" * 60)

    for i, entry in enumerate(entries, 1):
        click.echo(f"\n{i}. Pattern: {entry.pattern}")
        click.echo(f"   Reason: {entry.reason}")
        click.echo(f"   Added by: {entry.added_by}")
        if entry.file_path:
            click.echo(f"   File: {entry.file_path}")


@allowlist.command("add")
@click.argument("pattern")
@click.option("--reason", "-r", required=True, help="Why this secret is allowed")
@click.option("--added-by", "-a", required=True, help="Who is adding this entry")
@click.option("--file", "-f", help="Restrict to specific file")
def allowlist_add(pattern: str, reason: str, added_by: str, file: str | None) -> None:
    """Add an entry to the allowlist."""
    entry = add_to_allowlist(
        pattern=pattern,
        reason=reason,
        added_by=added_by,
        file_path=file,
    )
    click.echo(f"Added allowlist entry for pattern: {entry.pattern}")


@main.command("sync")
@click.argument("env_file", default=".env.local")
@click.option("--provider", "-p", help="Target provider (github, vercel, fly)")
@click.option("--environment", "-e", default="production", help="Target environment")
@click.option("--app", "-a", help="Override the config-resolved app (fly provider only)")
@click.option(
    "--only",
    help="Comma-separated key names to sync (fly provider only); others are skipped",
)
@click.option("--dry-run", is_flag=True, help="Show what would be synced")
@click.option("--interactive", "-i", is_flag=True, help="Interactive mode with provider selection")
def sync(
    env_file: str,
    provider: str | None,
    environment: str,
    app: str | None,
    only: str | None,
    dry_run: bool,
    interactive: bool,
) -> None:
    """Sync secrets from local env file to a provider."""
    from pathlib import Path

    env_path = Path(env_file)
    if not env_path.exists():
        click.echo(f"File not found: {env_file}", err=True)
        sys.exit(1)

    # Interactive provider selection
    if not provider:
        if interactive:
            available = ["github", "vercel", "fly"]
            click.echo("Available providers:")
            for i, p in enumerate(available, 1):
                click.echo(f"  {i}. {p}")
            choice = click.prompt("Select provider", type=int)
            if 1 <= choice <= len(available):
                provider = available[choice - 1]
            else:
                click.echo("Invalid selection.", err=True)
                sys.exit(1)
        else:
            click.echo(
                "Error: --provider is required. Use --interactive for guided selection.",
                err=True,
            )
            sys.exit(1)

    # --app and --only are fly-specific; reject them for other providers rather
    # than silently ignoring (they would otherwise have no effect).
    if (app or only) and provider != "fly":
        click.echo("Error: --app/--only are only supported for the fly provider.", err=True)
        sys.exit(1)

    only_keys = [k.strip() for k in only.split(",") if k.strip()] if only else None

    # Parse env file
    secrets_to_sync = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                secrets_to_sync[key.strip()] = value.strip().strip("\"'")

    if only_keys is not None:
        missing = [k for k in only_keys if k not in secrets_to_sync]
        if missing:
            click.echo(f"Warning: keys not found in {env_file}: {', '.join(missing)}", err=True)
        secrets_to_sync = {k: v for k, v in secrets_to_sync.items() if k in only_keys}

    if not secrets_to_sync:
        click.echo(f"No secrets found in {env_file}")
        return

    # Resolve the fly app (flag overrides config) for display and sync.
    resolved_app = app
    if provider == "fly" and not resolved_app:
        config = load_config()
        resolved_app = config.get("deployment", {}).get("fly", {}).get("app_name")

    click.echo(f"Found {len(secrets_to_sync)} secrets to sync:")
    for key in secrets_to_sync:
        click.echo(f"  - {key}")

    if dry_run:
        if provider == "fly":
            click.echo(f"\n(dry run - would sync to fly app '{resolved_app}')")
        else:
            click.echo(f"\n(dry run - would sync to {provider}/{environment})")
        return

    # Instantiate the provider
    from vibe.secrets.providers.base import SecretProvider

    prov: SecretProvider
    if provider == "github":
        from vibe.secrets.providers.github import GitHubSecretsProvider

        config = load_config()
        github_config = config.get("github", {})
        prov = GitHubSecretsProvider(
            owner=github_config.get("owner"),
            repo=github_config.get("repo"),
        )
    elif provider == "vercel":
        from vibe.secrets.providers.vercel import VercelSecretsProvider

        prov = VercelSecretsProvider()
    elif provider == "fly":
        from vibe.secrets.providers.fly import FlySecretsProvider

        prov = FlySecretsProvider(app_name=resolved_app)
    else:
        click.echo(f"Unknown provider: {provider}", err=True)
        sys.exit(1)

    if not prov.authenticate():
        click.echo(f"Not authenticated with {provider}. Check your credentials.", err=True)
        sys.exit(1)

    from vibe.secrets.providers.fly import FlySecretsProvider

    if isinstance(prov, FlySecretsProvider):
        results = prov.sync_from_local(env_file, environment, only=only_keys)
    else:
        results = prov.sync_from_local(env_file, environment)
    succeeded = sum(1 for v in results.values() if v)
    failed = sum(1 for v in results.values() if not v)
    click.echo(f"\nSynced {succeeded}/{len(results)} secrets to {provider}.")
    if failed:
        click.echo(f"{failed} secret(s) failed to sync.")
        for key, success in results.items():
            if not success:
                click.echo(f"  - {key}: FAILED", err=True)


if __name__ == "__main__":
    main()
