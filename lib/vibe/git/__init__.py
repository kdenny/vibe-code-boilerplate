"""Git operations including worktrees and branch management."""

from lib.vibe.git.branches import (
    create_branch,
    current_branch,
    delete_branch,
    format_branch_name,
    rebase_onto_main,
)
from lib.vibe.git.worktrees import (
    cleanup_worktree,
    create_worktree,
    list_worktrees,
)

__all__ = [
    "create_branch",
    "current_branch",
    "delete_branch",
    "format_branch_name",
    "rebase_onto_main",
    "create_worktree",
    "cleanup_worktree",
    "list_worktrees",
]
