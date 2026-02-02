"""Secret management utilities."""

from lib.vibe.secrets.allowlist import (
    add_to_allowlist,
    is_allowed_secret,
    load_allowlist,
    validate_allowlist,
)

__all__ = [
    "load_allowlist",
    "is_allowed_secret",
    "add_to_allowlist",
    "validate_allowlist",
]
