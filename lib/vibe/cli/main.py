"""Main CLI entry point for vibe commands."""

import sys
from pathlib import Path

import click

from lib.vibe.doctor import print_results, run_doctor
from lib.vibe.wizards.setup import run_individual_wizard, run_setup


@click.group()
@click.version_option(version="0.1.0", prog_name="vibe")
def main() -> None:
    """Vibe Code Boilerplate - AI-assisted development workflows."""
    pass


@main.command()
@click.option("--force", "-f", is_flag=True, help="Force reconfiguration")
@click.option("--wizard", "-w", help="Run a specific wizard (github, tracker, branch, env)")
def setup(force: bool, wizard: str | None) -> None:
    """Run the setup wizard to configure your project."""
    if wizard:
        success = run_individual_wizard(wizard)
    else:
        success = run_setup(force=force)

    sys.exit(0 if success else 1)


@main.command()
@click.option("--verbose", "-v", is_flag=True, help="Show verbose output")
def doctor(verbose: bool) -> None:
    """Check project health and configuration."""
    results = run_doctor(verbose=verbose)
    sys.exit(print_results(results))


@main.command()
@click.argument("ticket_id")
def do(ticket_id: str) -> None:
    """Start working on a ticket (creates worktree and branch from latest main)."""
    import subprocess

    from lib.vibe.config import load_config
    from lib.vibe.git.branches import format_branch_name, get_main_branch
    from lib.vibe.git.worktrees import create_worktree
    from lib.vibe.trackers.linear import LinearTracker

    config = load_config()
    tracker_type = config.get("tracker", {}).get("type")

    # Get ticket info if tracker configured
    title = None
    if tracker_type == "linear":
        tracker = LinearTracker()
        ticket = tracker.get_ticket(ticket_id)
        if ticket:
            title = ticket.title
            click.echo(f"Found ticket: {ticket.title}")

    # Create branch name
    branch_name = format_branch_name(ticket_id, title)
    click.echo(f"Branch: {branch_name}")

    # Fetch latest main so new branch is based on origin/main
    main_branch = get_main_branch()
    try:
        subprocess.run(
            ["git", "fetch", "origin", main_branch],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as e:
        click.echo(f"Warning: could not fetch origin/{main_branch}: {e}", err=True)

    # Create worktree from origin/main so branch is rebased to latest main
    origin_main = f"origin/{main_branch}"
    try:
        worktree = create_worktree(branch_name, base_branch=origin_main)
        click.echo(f"Worktree created at: {worktree.path}")
        click.echo(f"\nTo start working:\n  cd {worktree.path}")
    except Exception as e:
        click.echo(f"Failed to create worktree: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--title", "-t", help="PR title (default: branch name or branch + first commit line)")
@click.option("--body", "-b", help="PR body (default: use template)")
@click.option("--web", is_flag=True, help="Open PR form in the browser")
def pr(title: str | None, body: str | None, web: bool) -> None:
    """Open a pull request for the current branch (run from your worktree when done)."""
    import subprocess

    from lib.vibe.git.branches import current_branch, get_main_branch

    main_branch = get_main_branch()
    branch = current_branch()
    if branch == main_branch:
        click.echo(
            f"Cannot open PR from {main_branch}. Check out your feature branch first.", err=True
        )
        sys.exit(1)

    args = ["gh", "pr", "create"]
    if title:
        args.extend(["--title", title])
    else:
        args.extend(["--title", branch])  # default: branch name as title
    if body:
        args.extend(["--body", body])
    else:
        # Use PR template if it exists
        template = Path(".github/PULL_REQUEST_TEMPLATE.md")
        if template.exists():
            args.extend(["--body-file", str(template)])
    if web:
        args.append("--web")

    try:
        subprocess.run(args, check=True)
        click.echo("PR created.")
    except subprocess.CalledProcessError as e:
        click.echo(f"Failed to create PR: {e}", err=True)
        click.echo("Run: gh pr create")
        sys.exit(1)
    except FileNotFoundError:
        click.echo("gh CLI not found. Install it: https://cli.github.com/")
        click.echo("Then run: gh pr create")
        sys.exit(1)


# NOTE: These URLs point to the vibe-code-boilerplate repository itself, NOT the user's
# project. They're used for reporting bugs/issues with the boilerplate (broken recipes,
# CLAUDE.md errors, etc.). Users who fork the boilerplate keep these URLs so they can
# report upstream issues. Project-specific issues should use the project's own GitHub repo.
BOILERPLATE_ISSUES_URL = "https://github.com/kdenny/vibe-code-boilerplate/issues"
BOILERPLATE_NEW_ISSUE_URL = "https://github.com/kdenny/vibe-code-boilerplate/issues/new"


@main.command()
@click.option("--title", "-t", help="Pre-fill issue title")
@click.option("--body", "-b", help="Pre-fill issue body (or path to file with body)")
@click.option("--print-only", is_flag=True, help="Print URL only, do not open browser")
def boilerplate_issue(title: str | None, body: str | None, print_only: bool) -> None:
    """Open the boilerplate repo's new-issue page (for reporting broken CLAUDE.md or recipes)."""
    from urllib.parse import quote

    try:
        from lib.vibe.config import load_config

        config = load_config()
        base = (config.get("boilerplate") or {}).get("issues_url") or BOILERPLATE_ISSUES_URL
        new_issue = base.rstrip("/").replace("/issues", "") + "/issues/new"
    except Exception:
        new_issue = BOILERPLATE_NEW_ISSUE_URL

    params = []
    if title:
        params.append(f"title={quote(title)}")
    if body:
        if body.startswith("@") or "/" in body:
            try:
                with open(body.lstrip("@")) as f:
                    body = f.read()
            except OSError:
                pass
        params.append(f"body={quote(body)}")
    if params:
        new_issue += "?" + "&".join(params)

    if print_only:
        click.echo(new_issue)
        return

    try:
        import webbrowser

        webbrowser.open(new_issue)
        click.echo("Opened boilerplate repo new-issue page in your browser.")
        click.echo("If it did not open, use: " + new_issue)
    except Exception:
        click.echo("Could not open browser. File an issue manually at:")
        click.echo(new_issue)


@main.group()
def secrets() -> None:
    """Manage secrets and environment variables."""
    pass


@secrets.command("list")
@click.option("--provider", "-p", help="Filter by provider (github, vercel, fly)")
def secrets_list(provider: str | None) -> None:
    """List configured secrets."""
    from lib.vibe.config import load_config

    config = load_config()
    providers = config.get("secrets", {}).get("providers", [])

    if not providers:
        click.echo("No secret providers configured.")
        click.echo("Run 'bin/vibe setup' to configure providers.")
        return

    click.echo(f"Configured providers: {', '.join(providers)}")

    if provider and provider not in providers:
        click.echo(f"Provider '{provider}' not configured.")
        return

    # TODO: Implement listing from each provider
    click.echo("\nSecret listing not yet fully implemented.")


@secrets.command("sync")
@click.argument("env_file", default=".env.local")
@click.option("--provider", "-p", required=True, help="Target provider")
@click.option("--environment", "-e", default="repository", help="Target environment")
def secrets_sync(env_file: str, provider: str, environment: str) -> None:
    """Sync secrets from a local env file to a provider."""
    click.echo(f"Syncing {env_file} to {provider}/{environment}...")
    click.echo("Secret syncing not yet fully implemented.")


if __name__ == "__main__":
    main()
