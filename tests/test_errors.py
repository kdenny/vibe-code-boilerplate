"""Tests for public Vibe errors."""

from vibe.errors import MissingExtraError


def test_missing_extra_error_message_is_actionable() -> None:
    error = MissingExtraError("pr-autopilot", "pr-autopilot")

    assert "integration 'pr-autopilot' requires its extra" in str(error)
    assert "uv pip install 'vibe[pr-autopilot]'" in str(error)
