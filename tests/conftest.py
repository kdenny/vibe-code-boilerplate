"""Shared test fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _hermetic_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep CLI tests hermetic and free of cross-test interference.

    - ``VIBE_NO_CACHE`` disables file-based caching so tests don't leak state.
    - ``VIBE_NO_UPDATE_CHECK`` suppresses the boilerplate update-check banner.
      Without it, any branch whose ``VERSION`` is behind upstream prints the
      notice to stderr, which Click's ``CliRunner`` mixes into ``result.output``
      and breaks tests that parse a command's stdout (e.g. ``--json`` output).
    """
    monkeypatch.setenv("VIBE_NO_CACHE", "1")
    monkeypatch.setenv("VIBE_NO_UPDATE_CHECK", "1")
