"""Automatic update check for downstream boilerplate projects."""

import logging
import os
from datetime import datetime, timedelta
from typing import Any

import requests

from lib.vibe.config import load_config
from lib.vibe.state import load_state, save_state
from lib.vibe.version import get_version

logger = logging.getLogger(__name__)

# Default upstream repo for version checks
DEFAULT_UPSTREAM_REPO = "kdenny/vibe-code-boilerplate"
CHECK_INTERVAL_DAYS = 7
GITHUB_RAW_URL = "https://raw.githubusercontent.com/{repo}/main/VERSION"


def _compare_versions(local: str, remote: str) -> bool:
    """Return True if remote version is newer than local."""
    try:
        local_parts = [int(x) for x in local.split(".")]
        remote_parts = [int(x) for x in remote.split(".")]
        return remote_parts > local_parts
    except (ValueError, IndexError):
        return False


def _should_check(state: dict[str, Any]) -> bool:
    """Return True if enough time has passed since last check."""
    last_check = state.get("boilerplate_last_check")
    if not last_check:
        return True
    try:
        last_dt = datetime.fromisoformat(last_check)
        return datetime.now() - last_dt > timedelta(days=CHECK_INTERVAL_DAYS)
    except (ValueError, TypeError):
        return True


def _fetch_upstream_version(repo: str) -> str | None:
    """Fetch the latest VERSION from the upstream repo. Returns None on failure."""
    url = GITHUB_RAW_URL.format(repo=repo)
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        version: str = response.text.strip()
        return version
    except (requests.RequestException, OSError):
        return None


def check_for_update(force: bool = False) -> dict[str, Any] | None:
    """Check if a boilerplate update is available.

    Returns a dict with update info if an update is available, None otherwise.
    Silently returns None on any error (non-blocking).

    Args:
        force: If True, skip the time-based check interval.
    """
    if os.environ.get("VIBE_NO_UPDATE_CHECK") == "1":
        return None

    try:
        state = load_state()

        if not force and not _should_check(state):
            # Check if we already know about an available update
            upstream = state.get("boilerplate_upstream_version")
            current = get_version()
            if upstream and _compare_versions(current, upstream):
                return {
                    "current_version": current,
                    "upstream_version": upstream,
                    "cached": True,
                }
            return None

        # Determine upstream repo
        config = load_config()
        repo = config.get("boilerplate", {}).get("source_repo", DEFAULT_UPSTREAM_REPO)

        upstream_version = _fetch_upstream_version(repo)

        # Update state with check timestamp
        state["boilerplate_last_check"] = datetime.now().isoformat()
        if upstream_version:
            state["boilerplate_upstream_version"] = upstream_version
        state["boilerplate_current_version"] = get_version()
        save_state(state)

        if upstream_version and _compare_versions(get_version(), upstream_version):
            return {
                "current_version": get_version(),
                "upstream_version": upstream_version,
                "cached": False,
            }
        return None

    except Exception:
        # Never let update check break the user's workflow
        logger.debug("Update check failed", exc_info=True)
        return None


def skip_update_check() -> None:
    """Reset the check timer so the notice is dismissed for another interval."""
    state = load_state()
    state["boilerplate_last_check"] = datetime.now().isoformat()
    # Clear the upstream version so the notice doesn't re-appear from cache
    state.pop("boilerplate_upstream_version", None)
    save_state(state)


def format_update_notice(update_info: dict[str, Any]) -> str:
    """Format a user-friendly update notice."""
    current = update_info["current_version"]
    upstream = update_info["upstream_version"]
    return (
        f"\n  Boilerplate update available: {current} -> {upstream}\n"
        f"  Run `bin/vibe update` to sync, or `bin/vibe update --skip` to dismiss.\n"
    )
