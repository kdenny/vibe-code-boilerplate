"""GitHub authentication wizard."""

import subprocess
from typing import Any

import click

from lib.vibe.tools import require_interactive


def run_github_wizard(config: dict[str, Any]) -> bool:
    """
    Configure GitHub authentication.

    Args:
        config: Configuration dict to update

    Returns:
        True if configuration was successful
    """
    # Check prerequisites
    ok, error = require_interactive("GitHub")
    if not ok:
        click.echo(f"\n{error}")
        return False

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


def try_auto_configure_github(config: dict[str, Any]) -> bool:
    """
    Auto-configure GitHub from gh CLI and git remote (no prompts).

    Sets config["github"] with auth_method, owner, repo when both gh is
    authenticated and origin remote points to GitHub. Returns True if
    configuration was applied.
    """
    if not check_gh_cli_auth():
        return False
    owner, repo = _detect_remote()
    if not owner or not repo:
        return False
    config["github"]["auth_method"] = "gh_cli"
    config["github"]["owner"] = owner
    config["github"]["repo"] = repo
    return True


def dependency_graph_status(owner: str, repo: str) -> str | None:
    """
    Get Dependency graph status for the repo via GitHub API.

    Returns "enabled", "disabled", or None (API error or not available).
    """
    try:
        result = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{owner}/{repo}",
                "--jq",
                ".security_and_analysis.dependency_graph.status",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().strip('"')
        return None
    except FileNotFoundError:
        return None


def enable_dependency_graph_api(owner: str, repo: str) -> bool:
    """
    Enable Dependency graph for the repo via GitHub API.

    Requires repo admin. Returns True if enabled, False otherwise.
    """
    body = '{"security_and_analysis":{"dependency_graph":{"status":"enabled"}}}'
    try:
        result = subprocess.run(
            [
                "gh",
                "api",
                f"repos/{owner}/{repo}",
                "-X",
                "PATCH",
                "--input",
                "-",
            ],
            input=body,
            capture_output=True,
            text=True,
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def dependency_graph_settings_url(owner: str, repo: str) -> str:
    """URL to repo Settings > Code security and analysis."""
    return f"https://github.com/{owner}/{repo}/settings/security_analysis"


def run_dependency_graph_prompt(config: dict[str, Any]) -> None:
    """
    If GitHub is configured, check Dependency graph and optionally prompt to enable.

    - If already enabled: no prompt.
    - If disabled or unknown: prompt "Enable Dependency graph for security scanning?
      (requires repo admin)". On yes: try API; on failure or no, offer to open settings URL.
    """
    github = config.get("github") or {}
    owner = (github.get("owner") or "").strip()
    repo = (github.get("repo") or "").strip()
    if not owner or not repo:
        return

    if config.get("github", {}).get("auth_method") != "gh_cli":
        return

    status = dependency_graph_status(owner, repo)
    if status == "enabled":
        click.echo("  • Dependency graph: already enabled")
        return

    click.echo()
    click.echo(
        "Dependency graph is required for the Dependency Review GitHub Action (security.yml)."
    )
    click.echo("Without it, PRs will fail the Dependency Review check.")
    if not click.confirm(
        "Enable Dependency graph for security scanning? (requires repo admin)",
        default=True,
    ):
        click.echo(
            "  • Dependency graph: skipped. Enable later at Settings > Code security and analysis."
        )
        return

    if enable_dependency_graph_api(owner, repo):
        click.echo("  • Dependency graph: enabled")
        return

    click.echo("Could not enable via API (may need repo admin).")
    url = dependency_graph_settings_url(owner, repo)
    if click.confirm("Open repository settings in your browser?", default=True):
        try:
            subprocess.run(
                ["gh", "browser", url],
                check=False,
                capture_output=True,
            )
        except FileNotFoundError:
            click.echo(f"Open this URL: {url}")
    else:
        click.echo(f"Enable manually: {url}")


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
