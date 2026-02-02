"""GitHub authentication wizard."""

import subprocess
from typing import Any

import click


def run_github_wizard(config: dict[str, Any]) -> bool:
    """
    Configure GitHub authentication.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    click.echo("GitHub is used for repository access and CI/CD.")
    click.echo()

    # Check for existing gh CLI auth
    gh_authenticated = check_gh_cli_auth()

    if gh_authenticated:
        username = get_gh_username()
        click.echo(f"Detected: gh CLI is authenticated as '{username}'")
        if click.confirm("Use gh CLI for GitHub authentication?", default=True):
            config["github"]["auth_method"] = "gh_cli"
            _configure_repo(config)
            return True

    # Offer auth methods
    click.echo("\nAuthentication options:")
    click.echo("  1. GitHub CLI (gh) - Recommended")
    click.echo("  2. Personal Access Token (PAT)")

    choice = click.prompt("Select option", type=int, default=1)

    if choice == 1:
        return _setup_gh_cli(config)
    elif choice == 2:
        return _setup_pat(config)
    else:
        click.echo("Invalid choice")
        return False


def check_gh_cli_auth() -> bool:
    """Check if gh CLI is installed and authenticated."""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def get_gh_username() -> str | None:
    """Get the authenticated GitHub username from gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass
    return None


def _setup_gh_cli(config: dict[str, Any]) -> bool:
    """Set up GitHub authentication via gh CLI."""
    click.echo("\nTo authenticate with gh CLI, run:")
    click.echo("  gh auth login")
    click.echo()

    if check_gh_cli_auth():
        click.echo("gh CLI is already authenticated!")
        config["github"]["auth_method"] = "gh_cli"
        _configure_repo(config)
        return True

    click.echo("Please authenticate with gh CLI and run setup again.")
    return False


def _setup_pat(config: dict[str, Any]) -> bool:
    """Set up GitHub authentication via Personal Access Token."""
    click.echo("\nTo use a Personal Access Token:")
    click.echo("  1. Go to https://github.com/settings/tokens")
    click.echo("  2. Generate a token with 'repo' scope")
    click.echo("  3. Add to .env.local: GITHUB_TOKEN=ghp_xxxxx")
    click.echo()
    click.echo("Note: Never commit your token to version control!")
    click.echo()

    if click.confirm("Have you set up your GITHUB_TOKEN?", default=False):
        config["github"]["auth_method"] = "pat"
        _configure_repo(config)
        return True

    return False


def _configure_repo(config: dict[str, Any]) -> None:
    """Configure repository owner and name."""
    # Try to detect from git remote
    owner, repo = _detect_remote()

    if owner and repo:
        click.echo(f"\nDetected repository: {owner}/{repo}")
        if click.confirm("Is this correct?", default=True):
            config["github"]["owner"] = owner
            config["github"]["repo"] = repo
            return

    # Manual entry
    config["github"]["owner"] = click.prompt("GitHub owner (user or org)")
    config["github"]["repo"] = click.prompt("Repository name")


def _detect_remote() -> tuple[str | None, str | None]:
    """Detect GitHub owner/repo from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return None, None

        url = result.stdout.strip()

        # Parse SSH format: git@github.com:owner/repo.git
        if url.startswith("git@github.com:"):
            parts = url[15:].rstrip(".git").split("/")
            if len(parts) == 2:
                return parts[0], parts[1]

        # Parse HTTPS format: https://github.com/owner/repo.git
        if "github.com/" in url:
            parts = url.split("github.com/")[1].rstrip(".git").split("/")
            if len(parts) >= 2:
                return parts[0], parts[1]

    except (FileNotFoundError, subprocess.CalledProcessError):
        pass

    return None, None
