"""Tests for doctor health checks."""

from pathlib import Path

import pytest

from lib.vibe.doctor import (
    CheckResult,
    Status,
    check_config_exists,
    check_github_config,
    check_python_version,
    check_tracker_config,
)


class TestCheckPythonVersion:
    """Tests for check_python_version."""

    def test_check_python_version_passes(self) -> None:
        """Current Python should pass the version check (tests require 3.11+)."""
        result = check_python_version()
        assert result.status == Status.PASS
        assert "Python" in result.message

    def test_check_python_version_returns_check_result(self) -> None:
        """check_python_version returns a CheckResult."""
        result = check_python_version()
        assert isinstance(result, CheckResult)
        assert result.name == "Python version"


class TestCheckTrackerConfig:
    """Tests for check_tracker_config."""

    def test_check_tracker_config_no_tracker(self) -> None:
        """No tracker configured returns SKIP."""
        config: dict = {"tracker": {"type": None}}
        result = check_tracker_config(config)
        assert result.status == Status.SKIP
        assert result.category == "integration"

    def test_check_tracker_config_empty_tracker(self) -> None:
        """Empty tracker section returns SKIP."""
        config: dict = {}
        result = check_tracker_config(config)
        assert result.status == Status.SKIP

    def test_check_tracker_config_linear_no_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Linear configured without API key returns WARN."""
        monkeypatch.delenv("LINEAR_API_KEY", raising=False)
        config = {"tracker": {"type": "linear"}}
        result = check_tracker_config(config)
        assert result.status == Status.WARN
        assert "LINEAR_API_KEY" in result.message

    def test_check_tracker_config_linear_with_key(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Linear configured with API key returns PASS."""
        monkeypatch.setenv("LINEAR_API_KEY", "test-fake-key")
        config = {"tracker": {"type": "linear"}}
        result = check_tracker_config(config)
        assert result.status == Status.PASS

    def test_check_tracker_config_shortcut_no_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Shortcut configured without API token returns WARN."""
        monkeypatch.delenv("SHORTCUT_API_TOKEN", raising=False)
        config = {"tracker": {"type": "shortcut"}}
        result = check_tracker_config(config)
        assert result.status == Status.WARN
        assert "SHORTCUT_API_TOKEN" in result.message

    def test_check_tracker_config_shortcut_with_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Shortcut configured with API token returns PASS."""
        monkeypatch.setenv("SHORTCUT_API_TOKEN", "test-fake-token")
        config = {"tracker": {"type": "shortcut"}}
        result = check_tracker_config(config)
        assert result.status == Status.PASS

    def test_check_tracker_config_unknown_type(self) -> None:
        """Unknown tracker type returns WARN."""
        config = {"tracker": {"type": "jira"}}
        result = check_tracker_config(config)
        assert result.status == Status.WARN
        assert "Unknown tracker type" in result.message


class TestCheckGithubConfig:
    """Tests for check_github_config."""

    def test_check_github_config_complete(self) -> None:
        """Complete GitHub config returns PASS."""
        config = {"github": {"auth_method": "gh_cli", "owner": "test", "repo": "repo"}}
        result = check_github_config(config)
        assert result.status == Status.PASS
        assert "test/repo" in result.message

    def test_check_github_config_missing_owner(self) -> None:
        """Missing owner returns WARN."""
        config = {"github": {"auth_method": "gh_cli", "owner": "", "repo": "repo"}}
        result = check_github_config(config)
        assert result.status == Status.WARN
        assert "owner/repo not set" in result.message

    def test_check_github_config_missing_repo(self) -> None:
        """Missing repo returns WARN."""
        config = {"github": {"auth_method": "gh_cli", "owner": "test", "repo": ""}}
        result = check_github_config(config)
        assert result.status == Status.WARN

    def test_check_github_config_no_auth_method(self) -> None:
        """No auth method returns FAIL."""
        config = {"github": {"auth_method": None, "owner": "test", "repo": "repo"}}
        result = check_github_config(config)
        assert result.status == Status.FAIL
        assert "not configured" in result.message

    def test_check_github_config_empty_section(self) -> None:
        """Empty github section returns FAIL."""
        config = {"github": {}}
        result = check_github_config(config)
        assert result.status == Status.FAIL

    def test_check_github_config_missing_section(self) -> None:
        """Missing github section returns FAIL."""
        config: dict = {}
        result = check_github_config(config)
        assert result.status == Status.FAIL


class TestCheckConfigExists:
    """Tests for check_config_exists."""

    def test_check_config_exists_pass(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Returns PASS when config file exists."""
        vibe_dir = tmp_path / ".vibe"
        vibe_dir.mkdir()
        (vibe_dir / "config.json").write_text("{}")

        monkeypatch.chdir(tmp_path)
        result = check_config_exists()
        assert result.status == Status.PASS

    def test_check_config_exists_fail(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Returns FAIL when config file is missing."""
        monkeypatch.chdir(tmp_path)
        result = check_config_exists()
        assert result.status == Status.FAIL
        assert result.fix_hint is not None


class TestCheckResultDataclass:
    """Tests for the CheckResult dataclass."""

    def test_check_result_defaults(self) -> None:
        """CheckResult has sensible defaults."""
        result = CheckResult(name="Test", status=Status.PASS, message="OK")
        assert result.fix_hint is None
        assert result.category == "general"

    def test_check_result_all_fields(self) -> None:
        """CheckResult accepts all fields."""
        result = CheckResult(
            name="Test",
            status=Status.WARN,
            message="Warning",
            fix_hint="Fix it",
            category="integration",
        )
        assert result.name == "Test"
        assert result.status == Status.WARN
        assert result.message == "Warning"
        assert result.fix_hint == "Fix it"
        assert result.category == "integration"


class TestStatusEnum:
    """Tests for the Status enum."""

    def test_status_values(self) -> None:
        """Status enum has expected values."""
        assert Status.PASS.value is not None
        assert Status.WARN.value is not None
        assert Status.FAIL.value is not None
        assert Status.SKIP.value is not None

    def test_all_statuses_distinct(self) -> None:
        """All status values are distinct."""
        values = [s.value for s in Status]
        assert len(values) == len(set(values))
