"""Branch management utilities."""

import re
import subprocess

from lib.vibe.config import load_config


def format_branch_name(ticket_id: str, title: str | None = None) -> str:
    """
    Format a branch name according to the configured pattern.

    Args:
        ticket_id: The ticket identifier (e.g., "PROJ-123")
        title: Optional title to include in branch name

    Returns:
        Formatted branch name
    """
    config = load_config()
    pattern = config.get("branching", {}).get("pattern", "{PROJ}-{num}")

    # Extract project prefix and number from ticket_id
    match = re.match(r"([A-Z]+)-(\d+)", ticket_id)
    if match:
        proj, num = match.groups()
        branch_name = pattern.replace("{PROJ}", proj).replace("{num}", num)
    else:
        # Fallback: use ticket_id as-is
        branch_name = ticket_id

    # Optionally append sanitized title
    if title:
        # Sanitize title for branch name
        sanitized = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower())
        sanitized = sanitized.strip("-")[:30]  # Limit length
        branch_name = f"{branch_name}-{sanitized}"

    return branch_name


def current_branch() -> str:
    """Get the current branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def get_main_branch() -> str:
    """Get the main branch name from config."""
    config = load_config()
    return config.get("branching", {}).get("main_branch", "main")


def create_branch(branch_name: str, base_branch: str | None = None) -> bool:
    """
    Create a new branch.

    Args:
        branch_name: Name of the branch to create
        base_branch: Branch to base on (defaults to main)

    Returns:
        True if successful
    """
    if base_branch is None:
        base_branch = get_main_branch()

    try:
        subprocess.run(
            ["git", "checkout", "-b", branch_name, base_branch],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def delete_branch(branch_name: str, force: bool = False) -> bool:
    """
    Delete a branch.

    Args:
        branch_name: Name of the branch to delete
        force: Force delete even if not merged

    Returns:
        True if successful
    """
    flag = "-D" if force else "-d"
    try:
        subprocess.run(
            ["git", "branch", flag, branch_name],
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def rebase_onto_main() -> tuple[bool, str]:
    """
    Rebase current branch onto main.

    Returns:
        Tuple of (success, message)
    """
    config = load_config()
    if not config.get("branching", {}).get("always_rebase", True):
        return True, "Rebasing disabled in config"

    main_branch = get_main_branch()
    current = current_branch()

    if current == main_branch:
        return True, f"Already on {main_branch}"

    try:
        # Fetch latest main
        subprocess.run(
            ["git", "fetch", "origin", main_branch],
            check=True,
            capture_output=True,
        )

        # Rebase onto main
        subprocess.run(
            ["git", "rebase", f"origin/{main_branch}"],
            check=True,
            capture_output=True,
        )

        return True, f"Successfully rebased onto {main_branch}"
    except subprocess.CalledProcessError as e:
        # Check if rebase is in progress
        subprocess.run(["git", "rebase", "--abort"], capture_output=True)
        return False, f"Rebase failed: {e.stderr.decode() if e.stderr else 'Unknown error'}"


def validate_branch_naming(branch_name: str) -> tuple[bool, str]:
    """
    Validate that a branch name follows the configured pattern.

    Returns:
        Tuple of (is_valid, message)
    """
    config = load_config()
    pattern = config.get("branching", {}).get("pattern", "{PROJ}-{num}")

    # Convert pattern to regex
    regex_pattern = pattern.replace("{PROJ}", r"[A-Z]+").replace("{num}", r"\d+")
    regex_pattern = f"^{regex_pattern}"

    if re.match(regex_pattern, branch_name):
        return True, "Branch name follows convention"
    else:
        return False, f"Branch name should match pattern: {pattern}"
