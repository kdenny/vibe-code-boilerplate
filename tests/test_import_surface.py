"""Tests for the public ``vibe`` package entrypoints."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def test_top_level_import_exposes_public_surface() -> None:
    import vibe
    from vibe import cli, config, errors

    assert vibe.__all__ == ["__version__", "cli", "config", "errors"]
    assert vibe.cli is cli
    assert vibe.config is config
    assert vibe.errors is errors
    assert isinstance(vibe.__version__, str)


def test_python_m_vibe_runs_cli_help() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    env = {**os.environ, "VIBE_NO_DOTENV": "1"}

    result = subprocess.run(
        [sys.executable, "-m", "vibe", "--help"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout
    assert "Vibe Code Boilerplate" in result.stdout
