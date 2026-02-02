"""Secrets CLI commands."""

import sys

import click

from lib.vibe.config import load_config
from lib.vibe.secrets.allowlist import add_to_allowlist, load_allowlist


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
            from lib.vibe.secrets.providers.github import GitHubSecretsProvider

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
@click.option("--provider", "-p", required=True, help="Target provider")
@click.option("--environment", "-e", default="repository", help="Target environment")
@click.option("--dry-run", is_flag=True, help="Show what would be synced")
def sync(env_file: str, provider: str, environment: str, dry_run: bool) -> None:
    """Sync secrets from local env file to a provider."""
    from pathlib import Path

    env_path = Path(env_file)
    if not env_path.exists():
        click.echo(f"File not found: {env_file}", err=True)
        sys.exit(1)

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

    if not secrets_to_sync:
        click.echo(f"No secrets found in {env_file}")
        return

    click.echo(f"Found {len(secrets_to_sync)} secrets to sync:")
    for key in secrets_to_sync:
        click.echo(f"  - {key}")

    if dry_run:
        click.echo("\n(dry run - no changes made)")
        return

    if provider == "github":
        from lib.vibe.secrets.providers.github import GitHubSecretsProvider

        config = load_config()
        github_config = config.get("github", {})
        gh = GitHubSecretsProvider(
            owner=github_config.get("owner"),
            repo=github_config.get("repo"),
        )

        results = gh.sync_from_local(env_file, environment)
        succeeded = sum(1 for v in results.values() if v)
        click.echo(f"\nSynced {succeeded}/{len(results)} secrets to GitHub.")
    else:
        click.echo(f"\nProvider '{provider}' sync not yet implemented.")


if __name__ == "__main__":
    main()
