"""Local state management for .vibe/local_state.json."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

STATE_PATH = Path(".vibe/local_state.json")

DEFAULT_STATE: dict[str, Any] = {
    "installed_tools": {},
    "active_worktrees": [],
    "last_doctor_run": None,
    "tracker_cache": {"last_sync": None, "tickets": []},
    "github_cache": {"authenticated": False, "username": None},
}


def get_state_path(base_path: Path | None = None) -> Path:
    """Get the path to the state file."""
    if base_path:
        return base_path / STATE_PATH
    return STATE_PATH


def state_exists(base_path: Path | None = None) -> bool:
    """Check if state file exists."""
    return get_state_path(base_path).exists()


def load_state(base_path: Path | None = None) -> dict[str, Any]:
    """Load local state from .vibe/local_state.json."""
    state_file = get_state_path(base_path)
    if not state_file.exists():
        return DEFAULT_STATE.copy()

    with open(state_file) as f:
        result: dict[str, Any] = json.load(f)
        return result


def save_state(state: dict[str, Any], base_path: Path | None = None) -> None:
    """Save local state to .vibe/local_state.json."""
    state_file = get_state_path(base_path)
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)
        f.write("\n")


def update_state(updates: dict[str, Any], base_path: Path | None = None) -> dict[str, Any]:
    """Update specific keys in the local state."""
    state = load_state(base_path)
    _deep_update(state, updates)
    save_state(state, base_path)
    return state


def _deep_update(base: dict, updates: dict) -> None:
    """Recursively update nested dictionaries."""
    for key, value in updates.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def add_worktree(worktree_path: str, base_path: Path | None = None) -> None:
    """Add a worktree to the active worktrees list."""
    state = load_state(base_path)
    if worktree_path not in state["active_worktrees"]:
        state["active_worktrees"].append(worktree_path)
        save_state(state, base_path)


def remove_worktree(worktree_path: str, base_path: Path | None = None) -> None:
    """Remove a worktree from the active worktrees list."""
    state = load_state(base_path)
    if worktree_path in state["active_worktrees"]:
        state["active_worktrees"].remove(worktree_path)
        save_state(state, base_path)


def set_last_doctor_run(base_path: Path | None = None) -> None:
    """Update the last doctor run timestamp."""
    state = load_state(base_path)
    state["last_doctor_run"] = datetime.now().isoformat()
    save_state(state, base_path)


def set_github_auth(username: str, base_path: Path | None = None) -> None:
    """Update GitHub authentication state."""
    state = load_state(base_path)
    state["github_cache"] = {"authenticated": True, "username": username}
    save_state(state, base_path)


def record_ticket_branch(
    ticket_id: str,
    branch_name: str,
    worktree_path: str | None = None,
    base_path: Path | None = None,
) -> None:
    """Record a ticket-to-branch mapping in local state.

    Entries are stored as a list per ticket so that multiple branches for
    the same ticket are preserved (e.g. when ``bin/vibe do`` and Claude
    Code's ``isolation: "worktree"`` both create branches).  This enables
    duplicate-PR detection.
    """
    state = load_state(base_path)
    if "ticket_branches" not in state:
        state["ticket_branches"] = {}

    state["ticket_branches"].setdefault(ticket_id, []).append(
        {
            "branch": branch_name,
            "worktree_path": worktree_path,
            "created_at": datetime.now().isoformat(),
        }
    )
    save_state(state, base_path)


def get_ticket_branch(ticket_id: str, base_path: Path | None = None) -> dict[str, str] | None:
    """Look up the most recent branch recorded for a ticket.

    Returns a dict with ``branch``, ``worktree_path``, and ``created_at``
    keys, or ``None`` if no mapping exists.  When multiple entries exist
    the last (most recent) one is returned.

    Handles backward compatibility: if the stored value is a plain dict
    (old format) it is returned directly.
    """
    state = load_state(base_path)
    entry = state.get("ticket_branches", {}).get(ticket_id)
    if entry is None:
        return None
    # Old format: single dict
    if isinstance(entry, dict):
        return entry
    # New format: list of dicts – return the most recent
    if isinstance(entry, list) and entry:
        result: dict[str, str] = entry[-1]
        return result
    return None


def get_branches_for_ticket(ticket_id: str, base_path: Path | None = None) -> list[dict[str, str]]:
    """Return all recorded branches whose ticket ID matches.

    Searches the ``ticket_branches`` mapping for entries that match
    *ticket_id*.  Useful for detecting when a second branch is created
    for the same ticket.

    Handles backward compatibility: if the stored value is a plain dict
    (old format) it is wrapped in a list.
    """
    state = load_state(base_path)
    ticket_branches = state.get("ticket_branches", {})
    results: list[dict[str, str]] = []
    for tid, value in ticket_branches.items():
        if tid == ticket_id:
            # Old format: single dict
            if isinstance(value, dict):
                results.append({"ticket_id": tid, **value})
            # New format: list of dicts
            elif isinstance(value, list):
                for info in value:
                    results.append({"ticket_id": tid, **info})
    return results
