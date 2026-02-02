"""Secret allowlist management."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from lib.vibe.config import load_config

ALLOWLIST_PATH = Path(".vibe/secrets.allowlist.json")


@dataclass
class AllowlistEntry:
    """An entry in the secrets allowlist."""

    pattern: str
    reason: str
    added_by: str
    file_path: str | None = None
    hash: str | None = None


def get_allowlist_path() -> Path:
    """Get the path to the allowlist file."""
    config = load_config()
    custom_path = config.get("secrets", {}).get("allowlist_path")
    if custom_path:
        return Path(custom_path)
    return ALLOWLIST_PATH


def load_allowlist() -> list[AllowlistEntry]:
    """Load the secrets allowlist."""
    allowlist_file = get_allowlist_path()
    if not allowlist_file.exists():
        return []

    with open(allowlist_file) as f:
        data = json.load(f)

    entries = []
    for entry in data.get("entries", []):
        entries.append(
            AllowlistEntry(
                pattern=entry.get("pattern", ""),
                reason=entry.get("reason", ""),
                added_by=entry.get("added_by", ""),
                file_path=entry.get("file_path"),
                hash=entry.get("hash"),
            )
        )
    return entries


def save_allowlist(entries: list[AllowlistEntry]) -> None:
    """Save the secrets allowlist."""
    allowlist_file = get_allowlist_path()
    allowlist_file.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "$schema": "./secrets.allowlist.schema.json",
        "version": "1.0.0",
        "description": "Allowlist for secrets that are intentionally committed",
        "entries": [
            {
                "pattern": e.pattern,
                "reason": e.reason,
                "added_by": e.added_by,
                "file_path": e.file_path,
                "hash": e.hash,
            }
            for e in entries
        ],
    }

    with open(allowlist_file, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def is_allowed_secret(
    secret_value: str,
    file_path: str | None = None,
) -> tuple[bool, AllowlistEntry | None]:
    """
    Check if a secret is in the allowlist.

    Args:
        secret_value: The secret value to check
        file_path: Optional file path where the secret was found

    Returns:
        Tuple of (is_allowed, matching_entry)
    """
    entries = load_allowlist()
    secret_hash = hashlib.sha256(secret_value.encode()).hexdigest()

    for entry in entries:
        # Check hash match
        if entry.hash and entry.hash == secret_hash:
            return True, entry

        # Check pattern match
        if entry.pattern and entry.pattern in secret_value:
            # If file_path is specified in entry, it must match
            if entry.file_path and file_path and entry.file_path != file_path:
                continue
            return True, entry

    return False, None


def add_to_allowlist(
    pattern: str,
    reason: str,
    added_by: str,
    file_path: str | None = None,
    secret_value: str | None = None,
) -> AllowlistEntry:
    """
    Add an entry to the secrets allowlist.

    Args:
        pattern: Pattern to match (or description)
        reason: Why this secret is allowed
        added_by: Who added this entry
        file_path: Optional file path restriction
        secret_value: Optional secret value to hash

    Returns:
        The created AllowlistEntry
    """
    entries = load_allowlist()

    entry = AllowlistEntry(
        pattern=pattern,
        reason=reason,
        added_by=added_by,
        file_path=file_path,
        hash=hashlib.sha256(secret_value.encode()).hexdigest() if secret_value else None,
    )

    entries.append(entry)
    save_allowlist(entries)

    return entry


def validate_allowlist() -> tuple[bool, list[str]]:
    """
    Validate the allowlist structure.

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []
    allowlist_file = get_allowlist_path()

    if not allowlist_file.exists():
        return True, []  # No allowlist is valid

    try:
        with open(allowlist_file) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]

    if "entries" not in data:
        issues.append("Missing 'entries' key")

    for i, entry in enumerate(data.get("entries", [])):
        if not entry.get("pattern") and not entry.get("hash"):
            issues.append(f"Entry {i}: must have 'pattern' or 'hash'")
        if not entry.get("reason"):
            issues.append(f"Entry {i}: missing 'reason'")
        if not entry.get("added_by"):
            issues.append(f"Entry {i}: missing 'added_by'")

    return len(issues) == 0, issues
