"""GitHub Actions initialization utilities."""

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InitResult:
    """Result of GitHub Actions initialization."""

    success: bool
    workflows_copied: list[str]
    secrets_set: list[str]
    labels_created: list[str]
    errors: list[str]


# Core workflows that should be set up
CORE_WORKFLOWS = [
    "pr-policy.yml",
    "security.yml",
    "lint.yml",
    "tests.yml",
]

# Optional workflows (Linear integration)
LINEAR_WORKFLOWS = [
    "pr-opened.yml",
    "pr-merged.yml",
]

# All available workflows
ALL_WORKFLOWS = (
    CORE_WORKFLOWS
    + LINEAR_WORKFLOWS
    + [
        "human-followup-on-deployment.yml",
        "integration-freshness.yml",
    ]
)

# Required labels for PR policy
REQUIRED_LABELS = [
    ("Low Risk", "0e8a16", "Minimal scope, well-tested, low blast radius"),
    ("Medium Risk", "fbca04", "Moderate scope, may affect multiple components"),
    ("High Risk", "d93f0b", "Large scope, critical path, or infrastructure changes"),
    ("Bug", "d73a4a", "Something isn't working"),
    ("Feature", "a2eeef", "New feature or request"),
    ("Chore", "fef2c0", "Maintenance, dependencies, cleanup"),
    ("Refactor", "c5def5", "Code improvement, no behavior change"),
    ("HUMAN", "b60205", "Requires human decision or action"),
]


def get_boilerplate_workflows_dir() -> Path | None:
    """Get the path to boilerplate workflows directory."""
    # Try to find workflows relative to this file
    current_file = Path(__file__)
    boilerplate_root = current_file.parent.parent.parent
    workflows_dir = boilerplate_root / ".github" / "workflows"

    if workflows_dir.exists():
        return workflows_dir
    return None


def copy_workflows(
    target_dir: Path,
    workflows: list[str] | None = None,
    dry_run: bool = False,
) -> tuple[list[str], list[str]]:
    """
    Copy workflow files to target directory.

    Args:
        target_dir: Target .github/workflows directory
        workflows: List of workflow files to copy (default: CORE_WORKFLOWS)
        dry_run: If True, don't actually copy files

    Returns:
        Tuple of (copied files, errors)
    """
    source_dir = get_boilerplate_workflows_dir()
    if not source_dir:
        return [], ["Could not find boilerplate workflows directory"]

    workflows = workflows or CORE_WORKFLOWS
    copied = []
    errors = []

    target_dir.mkdir(parents=True, exist_ok=True)

    for workflow in workflows:
        source_file = source_dir / workflow
        target_file = target_dir / workflow

        if not source_file.exists():
            errors.append(f"Workflow not found: {workflow}")
            continue

        if target_file.exists():
            # Skip if already exists (don't overwrite)
            continue

        if dry_run:
            copied.append(workflow)
        else:
            try:
                shutil.copy2(source_file, target_file)
                copied.append(workflow)
            except OSError as e:
                errors.append(f"Failed to copy {workflow}: {e}")

    return copied, errors


def set_github_secret(name: str, value: str, dry_run: bool = False) -> bool:
    """Set a GitHub repository secret using gh CLI."""
    if dry_run:
        return True

    try:
        result = subprocess.run(
            ["gh", "secret", "set", name],
            input=value,
            text=True,
            capture_output=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def create_github_label(name: str, color: str, description: str, dry_run: bool = False) -> bool:
    """Create a GitHub label using gh CLI."""
    if dry_run:
        return True

    try:
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
                "--force",  # Update if exists
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def init_github_actions(
    project_path: Path | None = None,
    include_linear: bool = False,
    linear_api_key: str | None = None,
    dry_run: bool = False,
) -> InitResult:
    """
    Initialize GitHub Actions for a project.

    Args:
        project_path: Project root (default: cwd)
        include_linear: Include Linear integration workflows
        linear_api_key: LINEAR_API_KEY to set as secret
        dry_run: Preview changes without applying

    Returns:
        InitResult with details of what was done
    """
    project_path = project_path or Path.cwd()
    workflows_dir = project_path / ".github" / "workflows"

    workflows_to_copy = list(CORE_WORKFLOWS)
    if include_linear:
        workflows_to_copy.extend(LINEAR_WORKFLOWS)

    errors = []
    secrets_set = []
    labels_created = []

    # Copy workflows
    copied, copy_errors = copy_workflows(workflows_dir, workflows_to_copy, dry_run)
    errors.extend(copy_errors)

    # Set secrets
    if linear_api_key and include_linear:
        if set_github_secret("LINEAR_API_KEY", linear_api_key, dry_run):
            secrets_set.append("LINEAR_API_KEY")
        else:
            errors.append("Failed to set LINEAR_API_KEY secret")

    # Create labels
    for name, color, description in REQUIRED_LABELS:
        if create_github_label(name, color, description, dry_run):
            labels_created.append(name)
        else:
            errors.append(f"Failed to create label: {name}")

    success = len(errors) == 0 or (len(copied) > 0 and len(errors) < len(workflows_to_copy))

    return InitResult(
        success=success,
        workflows_copied=copied,
        secrets_set=secrets_set,
        labels_created=labels_created,
        errors=errors,
    )
