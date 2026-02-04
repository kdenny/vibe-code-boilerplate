"""GitHub Actions initialization wizard."""

from __future__ import annotations

import subprocess
from pathlib import Path

import click

# Core workflows that should always be installed
CORE_WORKFLOWS = [
    "pr-policy.yml",
    "security.yml",
]

# Optional workflows based on project configuration
OPTIONAL_WORKFLOWS = {
    "tests.yml": "Test runner (requires tests to exist)",
    "lint.yml": "Python linting (for Python projects)",
    "pr-opened.yml": "Linear status: In Review on PR open",
    "pr-merged.yml": "Linear status: Deployed on PR merge",
    "human-followup-on-deployment.yml": "Create HUMAN ticket on deployment config merge",
}

# Required secrets for Linear integration
LINEAR_SECRETS = [
    ("LINEAR_API_KEY", "Linear API key (from Linear Settings → API)"),
]

# Required repository variables for Linear
LINEAR_VARIABLES = [
    ("LINEAR_TEAM_ID", "Linear team ID (from Linear Settings → Team)"),
]

# Labels to create
LABELS = {
    "type": [
        ("Bug", "d73a4a", "Something isn't working"),
        ("Feature", "0075ca", "New feature or request"),
        ("Chore", "fef2c0", "Maintenance, dependencies, cleanup"),
        ("Refactor", "c5def5", "Code improvement, no behavior change"),
    ],
    "risk": [
        ("Low Risk", "0e8a16", "Minimal scope, well-tested"),
        ("Medium Risk", "fbca04", "Moderate scope, may affect multiple components"),
        ("High Risk", "d93f0b", "Large scope, critical path, or infrastructure"),
    ],
    "area": [
        ("Frontend", "1d76db", "UI, client-side code"),
        ("Backend", "5319e7", "Server, API, business logic"),
        ("Infra", "006b75", "DevOps, CI/CD, infrastructure"),
        ("Docs", "0052cc", "Documentation only"),
    ],
    "special": [
        ("HUMAN", "d4c5f9", "Requires human decision/action"),
        ("Milestone", "bfdadc", "Part of a larger feature"),
        ("Blocked", "b60205", "Waiting on external dependency"),
    ],
}


def get_boilerplate_path() -> Path | None:
    """Try to find the boilerplate source directory."""
    # Check common locations
    candidates = [
        Path(__file__).parent.parent.parent.parent,  # lib/vibe/wizards -> root
        Path.home() / "vibe-code-boilerplate",
        Path("/usr/local/share/vibe-code-boilerplate"),
    ]

    for path in candidates:
        workflows_dir = path / ".github" / "workflows"
        if workflows_dir.exists() and (workflows_dir / "pr-policy.yml").exists():
            return path

    return None


def run_github_actions_wizard(dry_run: bool = False) -> bool:
    """Initialize GitHub Actions workflows, secrets, and labels.

    Args:
        dry_run: If True, show what would be done without making changes

    Returns:
        True if initialization completed successfully
    """
    click.echo("=" * 60)
    click.echo("  GitHub Actions Initialization")
    click.echo("=" * 60)
    click.echo()

    # Find boilerplate source
    boilerplate_path = get_boilerplate_path()
    if not boilerplate_path:
        click.secho("Could not find boilerplate source directory.", fg="red")
        click.echo("Ensure you're running from a project that includes the boilerplate,")
        click.echo("or specify --boilerplate-path.")
        return False

    workflows_source = boilerplate_path / ".github" / "workflows"
    click.echo(f"Using workflows from: {workflows_source}")
    click.echo()

    # Check gh CLI
    if not _check_gh_cli():
        click.secho("GitHub CLI (gh) not found or not authenticated.", fg="red")
        click.echo("Install: https://cli.github.com/")
        click.echo("Then run: gh auth login")
        return False

    # Get repo info
    repo = _get_current_repo()
    if not repo:
        click.secho("Could not determine current repository.", fg="red")
        click.echo("Ensure you're in a git repository with a GitHub remote.")
        return False

    click.echo(f"Repository: {repo}")
    click.echo()

    if dry_run:
        click.secho("DRY RUN - showing what would be done", fg="yellow")
        click.echo()

    # Step 1: Copy core workflows
    click.secho("Step 1: Core Workflows", fg="cyan", bold=True)
    _copy_workflows(workflows_source, CORE_WORKFLOWS, dry_run)

    # Step 2: Select optional workflows
    click.echo()
    click.secho("Step 2: Optional Workflows", fg="cyan", bold=True)
    selected_optional = _select_optional_workflows()
    if selected_optional:
        _copy_workflows(workflows_source, selected_optional, dry_run)

    # Step 3: Create labels
    click.echo()
    click.secho("Step 3: Labels", fg="cyan", bold=True)
    _create_labels(repo, dry_run)

    # Step 4: Configure secrets (if Linear workflows selected)
    has_linear = any(wf in selected_optional for wf in ["pr-opened.yml", "pr-merged.yml"])
    if has_linear:
        click.echo()
        click.secho("Step 4: Linear Integration", fg="cyan", bold=True)
        _configure_linear_secrets(repo, dry_run)

    click.echo()
    click.echo("=" * 60)
    if dry_run:
        click.secho("  Dry Run Complete", fg="yellow", bold=True)
        click.echo("  Run without --dry-run to apply changes")
    else:
        click.secho("  GitHub Actions Initialized!", fg="green", bold=True)
    click.echo("=" * 60)
    click.echo()

    if not dry_run:
        click.echo("Next steps:")
        click.echo("  1. Commit the workflow files: git add .github/workflows && git commit")
        click.echo("  2. Push to GitHub to activate workflows")
        if has_linear:
            click.echo("  3. Test by opening a PR with a Linear ticket in the branch name")

    return True


def _check_gh_cli() -> bool:
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


def _get_current_repo() -> str | None:
    """Get the current repository in owner/repo format."""
    try:
        result = subprocess.run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "-q", ".nameWithOwner"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return None


def _copy_workflows(source_dir: Path, workflows: list[str], dry_run: bool) -> None:
    """Copy workflow files to current project."""
    target_dir = Path(".github/workflows")

    for workflow in workflows:
        source_file = source_dir / workflow
        target_file = target_dir / workflow

        if not source_file.exists():
            click.echo(f"  {click.style('⚠', fg='yellow')} {workflow} - not found in source")
            continue

        if target_file.exists():
            click.echo(f"  {click.style('○', fg='blue')} {workflow} - already exists")
            continue

        if dry_run:
            click.echo(f"  {click.style('→', fg='cyan')} {workflow} - would copy")
        else:
            target_dir.mkdir(parents=True, exist_ok=True)
            target_file.write_text(source_file.read_text())
            click.echo(f"  {click.style('✓', fg='green')} {workflow} - copied")


def _select_optional_workflows() -> list[str]:
    """Let user select which optional workflows to install."""
    selected = []

    for workflow, description in OPTIONAL_WORKFLOWS.items():
        target = Path(".github/workflows") / workflow
        if target.exists():
            click.echo(f"  {click.style('○', fg='blue')} {workflow} - already exists")
            continue

        if click.confirm(f"  Install {workflow}? ({description})", default=True):
            selected.append(workflow)

    return selected


def _create_labels(repo: str, dry_run: bool) -> None:
    """Create labels in the repository."""
    for category, labels in LABELS.items():
        click.echo(f"  {category} labels:")
        for name, color, description in labels:
            if dry_run:
                click.echo(f"    {click.style('→', fg='cyan')} {name}")
            else:
                # Try to create label (will fail silently if exists)
                result = subprocess.run(
                    [
                        "gh",
                        "label",
                        "create",
                        name,
                        "--color",
                        color,
                        "--description",
                        description,
                        "--repo",
                        repo,
                    ],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    click.echo(f"    {click.style('✓', fg='green')} {name}")
                elif "already exists" in result.stderr.lower():
                    click.echo(f"    {click.style('○', fg='blue')} {name} (exists)")
                else:
                    click.echo(f"    {click.style('✗', fg='red')} {name} - {result.stderr.strip()}")


def _configure_linear_secrets(repo: str, dry_run: bool) -> None:
    """Configure Linear API secrets."""
    click.echo("  Linear integration requires:")
    click.echo("    - LINEAR_API_KEY (repository secret)")
    click.echo("    - LINEAR_TEAM_ID (repository variable)")
    click.echo()

    if dry_run:
        click.echo("  Would prompt for secrets to set via gh CLI")
        return

    # Check if secrets already exist
    for secret_name, description in LINEAR_SECRETS:
        click.echo(f"  {secret_name}: {description}")
        value = click.prompt(
            f"    Enter {secret_name} (or 'skip' to skip)",
            default="skip",
            hide_input=True,
            show_default=False,
        )
        if value and value.lower() != "skip":
            result = subprocess.run(
                ["gh", "secret", "set", secret_name, "--repo", repo, "--body", value],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                click.echo(f"    {click.style('✓', fg='green')} Set {secret_name}")
            else:
                click.echo(f"    {click.style('✗', fg='red')} Failed: {result.stderr.strip()}")
        else:
            click.echo(f"    {click.style('○', fg='blue')} Skipped")

    # Set variables
    for var_name, description in LINEAR_VARIABLES:
        click.echo(f"  {var_name}: {description}")
        value = click.prompt(
            f"    Enter {var_name} (or 'skip' to skip)",
            default="skip",
        )
        if value and value.lower() != "skip":
            result = subprocess.run(
                ["gh", "variable", "set", var_name, "--repo", repo, "--body", value],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                click.echo(f"    {click.style('✓', fg='green')} Set {var_name}")
            else:
                click.echo(f"    {click.style('✗', fg='red')} Failed: {result.stderr.strip()}")
        else:
            click.echo(f"    {click.style('○', fg='blue')} Skipped")
