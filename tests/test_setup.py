"""Tests for setup wizard auto-initialization (issue #6)."""

from pathlib import Path

from lib.vibe.config import DEFAULT_CONFIG, load_config
from lib.vibe.wizards.setup import (
    apply_git_workflow_defaults,
    ensure_commit_convention,
    ensure_local_state,
    ensure_pr_template,
    is_fresh_project,
)


def test_is_fresh_project_when_config_did_not_exist() -> None:
    config = load_config()
    assert is_fresh_project(config, config_file_existed=False) is True


def test_is_fresh_project_when_config_empty_github_no_tracker() -> None:
    config = {
        "github": {"auth_method": None, "owner": "", "repo": ""},
        "tracker": {"type": None, "config": {}},
    }
    assert is_fresh_project(config, config_file_existed=True) is True


def test_is_fresh_project_false_when_github_configured() -> None:
    config = {
        "github": {"auth_method": "gh_cli", "owner": "me", "repo": "myrepo"},
        "tracker": {"type": None, "config": {}},
    }
    assert is_fresh_project(config, config_file_existed=True) is False


def test_is_fresh_project_false_when_tracker_configured() -> None:
    config = {
        "github": {"auth_method": None, "owner": "", "repo": ""},
        "tracker": {"type": "linear", "config": {}},
    }
    assert is_fresh_project(config, config_file_existed=True) is False


def test_apply_git_workflow_defaults() -> None:
    config = {
        "branching": {"pattern": "custom", "main_branch": "master", "always_rebase": False},
        "worktrees": {"location": "custom", "base_path": "/tmp/x", "auto_cleanup": False},
    }
    apply_git_workflow_defaults(config)
    assert config["branching"] == dict(DEFAULT_CONFIG["branching"])
    assert config["worktrees"] == dict(DEFAULT_CONFIG["worktrees"])


def test_ensure_pr_template_creates_file_when_missing(tmp_path: Path) -> None:
    template_path = tmp_path / ".github" / "PULL_REQUEST_TEMPLATE.md"
    assert not template_path.exists()
    result = ensure_pr_template(tmp_path)
    assert result is True
    assert template_path.exists()
    content = template_path.read_text()
    assert "## Summary" in content
    assert "Risk Assessment" in content
    assert "Checklist" in content


def test_ensure_pr_template_does_not_overwrite_existing(tmp_path: Path) -> None:
    template_path = tmp_path / ".github" / "PULL_REQUEST_TEMPLATE.md"
    template_path.parent.mkdir(parents=True, exist_ok=True)
    custom = "Custom PR template"
    template_path.write_text(custom)
    result = ensure_pr_template(tmp_path)
    assert result is True
    assert template_path.read_text() == custom


def test_ensure_local_state_creates_file_when_missing(tmp_path: Path) -> None:
    state_path = tmp_path / ".vibe" / "local_state.json"
    assert not state_path.exists()
    result = ensure_local_state(tmp_path)
    assert result is True
    assert state_path.exists()
    import json

    data = json.loads(state_path.read_text())
    assert "active_worktrees" in data
    assert data["active_worktrees"] == []


def test_ensure_local_state_does_not_overwrite_existing(tmp_path: Path) -> None:
    state_path = tmp_path / ".vibe" / "local_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text('{"active_worktrees": ["/some/path"]}')
    result = ensure_local_state(tmp_path)
    assert result is True
    import json

    data = json.loads(state_path.read_text())
    assert data["active_worktrees"] == ["/some/path"]


def test_ensure_commit_convention_creates_file_when_missing(tmp_path: Path) -> None:
    path = tmp_path / ".github" / "COMMIT_CONVENTION.md"
    assert not path.exists()
    result = ensure_commit_convention(tmp_path)
    assert result is True
    assert path.exists()
    content = path.read_text()
    assert "TICKET-123" in content
    assert "Short description" in content


def test_ensure_commit_convention_does_not_overwrite_existing(tmp_path: Path) -> None:
    path = tmp_path / ".github" / "COMMIT_CONVENTION.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    custom = "Custom commit rules"
    path.write_text(custom)
    result = ensure_commit_convention(tmp_path)
    assert result is True
    assert path.read_text() == custom
