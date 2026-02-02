"""Git worktree management."""

import subprocess
from dataclasses import dataclass
from pathlib import Path

from lib.vibe.config import load_config
from lib.vibe.state import add_worktree, load_state, remove_worktree


@dataclass
class Worktree:
    """Represents a git worktree."""

    path: str
    branch: str
    commit: str
    is_main: bool = False


def get_worktree_base_path() -> Path:
    """Get the base path for worktrees from config."""
    config = load_config()
    base_path = config.get("worktrees", {}).get("base_path", "../{repo}-worktrees")

    # Resolve {repo} placeholder
    repo_name = Path.cwd().name
    base_path = base_path.replace("{repo}", repo_name)

    return Path(base_path).resolve()


def create_worktree(branch_name: str, base_branch: str = "main") -> Worktree:
    """
    Create a new git worktree for the given branch.

    Args:
        branch_name: Name of the branch to create/checkout
        base_branch: Branch to base the new branch on

    Returns:
        Worktree object with path and branch info
    """
    worktree_base = get_worktree_base_path()
    worktree_path = worktree_base / branch_name

    # Ensure base directory exists
    worktree_base.mkdir(parents=True, exist_ok=True)

    # Check if branch exists
    result = subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/heads/{branch_name}"],
        capture_output=True,
        text=True,
    )
    branch_exists = result.returncode == 0

    if branch_exists:
        # Checkout existing branch
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), branch_name],
            check=True,
            capture_output=True,
        )
    else:
        # Create new branch from base
        subprocess.run(
            ["git", "worktree", "add", "-b", branch_name, str(worktree_path), base_branch],
            check=True,
            capture_output=True,
        )

    # Get commit hash
    result = subprocess.run(
        ["git", "-C", str(worktree_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    commit = result.stdout.strip()

    # Track in state
    add_worktree(str(worktree_path))

    return Worktree(
        path=str(worktree_path),
        branch=branch_name,
        commit=commit,
        is_main=False,
    )


def cleanup_worktree(worktree_path: str, force: bool = False) -> bool:
    """
    Remove a git worktree.

    Args:
        worktree_path: Path to the worktree to remove
        force: Force removal even with uncommitted changes

    Returns:
        True if cleanup was successful
    """
    cmd = ["git", "worktree", "remove", worktree_path]
    if force:
        cmd.append("--force")

    try:
        subprocess.run(cmd, check=True, capture_output=True)
        remove_worktree(worktree_path)
        return True
    except subprocess.CalledProcessError:
        return False


def list_worktrees() -> list[Worktree]:
    """List all git worktrees."""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True,
        text=True,
        check=True,
    )

    worktrees = []
    current: dict[str, str] = {}

    for line in result.stdout.strip().split("\n"):
        if not line:
            if current:
                worktrees.append(
                    Worktree(
                        path=current.get("worktree", ""),
                        branch=current.get("branch", "").replace("refs/heads/", ""),
                        commit=current.get("HEAD", ""),
                        is_main="bare" in current,
                    )
                )
                current = {}
        elif line.startswith("worktree "):
            current["worktree"] = line[9:]
        elif line.startswith("HEAD "):
            current["HEAD"] = line[5:]
        elif line.startswith("branch "):
            current["branch"] = line[7:]
        elif line == "bare":
            current["bare"] = "true"

    # Don't forget the last one
    if current:
        worktrees.append(
            Worktree(
                path=current.get("worktree", ""),
                branch=current.get("branch", "").replace("refs/heads/", ""),
                commit=current.get("HEAD", ""),
                is_main="bare" in current,
            )
        )

    return worktrees


def cleanup_stale_worktrees() -> list[str]:
    """
    Cleanup worktrees tracked in state that no longer exist.

    Returns:
        List of cleaned up worktree paths
    """
    state = load_state()
    active = state.get("active_worktrees", [])
    cleaned = []

    for worktree_path in active:
        if not Path(worktree_path).exists():
            remove_worktree(worktree_path)
            cleaned.append(worktree_path)

    return cleaned
