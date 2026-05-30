"""Integration test for the ``git.worktrees`` ↔ ``state`` compose seam.

This is the first suite in the integration layer (VIBE-174) and exists to
*demonstrate the pattern*, not to be exhaustive.

Why it earns its place: the unit tests for ``git/worktrees.py`` mock out
``add_worktree`` (see ``tests/test_git_worktrees.py``), so the real seam between
worktree creation and local-state persistence is never exercised — exactly the
"mock the collaborator, not the boundary" gap the modular-testing policy warns
about. Here we let ``create_worktree`` drive the *real* ``state`` module and mock
only the git subprocess (the true I/O boundary), then assert the worktree was
actually persisted to ``.vibe/local_state.json`` on disk.

``state`` accepts a ``base_path``, and ``create_worktree`` forwards the primary
repo root as that base — so pointing the repo root at ``tmp_path`` keeps the
whole seam on a throwaway filesystem with no mocking of the collaborator.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from lib.vibe.git.worktrees import create_worktree
from lib.vibe.state import load_state


def _fake_git(commit: str):
    """A subprocess.run stand-in: branch is absent, HEAD resolves to *commit*."""

    def run(cmd, *args, **kwargs):  # type: ignore[no-untyped-def]
        result = MagicMock()
        # `rev-parse --verify refs/heads/<branch>` → non-zero means "new branch".
        if "rev-parse" in cmd and "--verify" in cmd:
            result.returncode = 1
        else:
            result.returncode = 0
        if "rev-parse" in cmd and "HEAD" in cmd:
            result.stdout = commit
        return result

    return run


def test_create_worktree_persists_to_real_state(tmp_path: Path) -> None:
    """create_worktree composes with the real state module and writes to disk.

    No mock of ``add_worktree`` — the assertion reads back the file the real
    state module wrote, proving the two modules actually compose.
    """
    repo_root = tmp_path
    worktree_base = tmp_path / "worktrees"

    with (
        patch("lib.vibe.git.worktrees.get_primary_repo_root", return_value=repo_root),
        patch("lib.vibe.git.worktrees.get_worktree_base_path", return_value=worktree_base),
        patch("lib.vibe.git.worktrees.subprocess.run", side_effect=_fake_git("abc123def")),
    ):
        wt = create_worktree("VIBE-999", "main")

    assert wt.commit == "abc123def"
    assert (repo_root / ".vibe" / "local_state.json").exists()

    persisted = load_state(repo_root)["active_worktrees"]
    assert wt.path in persisted
    # Recording is idempotent: state.add_worktree de-dupes, so a single entry.
    assert persisted.count(wt.path) == 1
