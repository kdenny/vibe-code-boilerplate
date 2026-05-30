"""Tests for lib/vibe/env.py — env loading and direnv setup (VIBE-176)."""

import subprocess
from pathlib import Path

from lib.vibe.env import check_direnv_status, setup_direnv


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(root), check=True, capture_output=True)


def _init_repo(root: Path) -> None:
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")


def test_setup_direnv_creates_envrc_and_ignores_it_when_untracked(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text("# existing\n", encoding="utf-8")

    result = setup_direnv(tmp_path)

    assert result["envrc_created"] is True
    assert (tmp_path / ".envrc").read_text(encoding="utf-8") == "dotenv_if_exists .env.local\n"
    # Language-agnostic downstream default: generated .envrc is gitignored.
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".envrc" in gitignore
    assert ".direnv/" in gitignore


def test_setup_direnv_does_not_reignore_committed_envrc(tmp_path: Path) -> None:
    # Simulate a repo (like VIBE itself) that commits its .envrc.
    _init_repo(tmp_path)
    (tmp_path / ".envrc").write_text("layout python3\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text("# no envrc line here\n", encoding="utf-8")
    _git(tmp_path, "add", ".envrc")

    result = setup_direnv(tmp_path)

    # Existing committed .envrc is left untouched...
    assert result["envrc_created"] is False
    assert (tmp_path / ".envrc").read_text(encoding="utf-8") == "layout python3\n"
    # ...and is NOT re-added to .gitignore, while .direnv/ still is.
    gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
    assert ".envrc\n" not in gitignore
    assert ".direnv/" in gitignore


def test_setup_direnv_is_idempotent_on_gitignore(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text(".envrc\n.direnv/\n", encoding="utf-8")

    result = setup_direnv(tmp_path)

    assert result["gitignore_updated"] is False
    # No duplicate lines appended.
    lines = (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert lines.count(".envrc") == 1
    assert lines.count(".direnv/") == 1


def test_check_direnv_status_reports_envrc_presence(tmp_path: Path) -> None:
    assert check_direnv_status(tmp_path)["envrc_exists"] is False

    (tmp_path / ".envrc").write_text("dotenv_if_exists .env.local\n", encoding="utf-8")
    status = check_direnv_status(tmp_path)
    assert status["envrc_exists"] is True
    # direnv_allowed is None unless direnv is installed AND has allowed the dir.
    assert "direnv_installed" in status
