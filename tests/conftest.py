"""Shared test fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _disable_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable file-based caching during tests to prevent cross-test interference."""
    monkeypatch.setenv("VIBE_NO_CACHE", "1")
