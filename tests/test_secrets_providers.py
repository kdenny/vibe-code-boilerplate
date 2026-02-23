"""Tests for secret providers and env file parsing."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from lib.vibe.secrets.allowlist import (
    AllowlistEntry,
    validate_allowlist,
)
from lib.vibe.secrets.providers.base import Secret
from lib.vibe.secrets.providers.fly import FlySecretsProvider
from lib.vibe.secrets.providers.github import GitHubSecretsProvider
from lib.vibe.secrets.providers.vercel import VercelSecretsProvider


class TestVercelParseEnvFile:
    """Tests for Vercel provider env file parsing."""

    def test_parse_basic_env_file(self, tmp_path: Path) -> None:
        """Parses simple KEY=value lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\nKEY2=value2\n")

        provider = VercelSecretsProvider()
        secrets = provider._parse_env_file(str(env_file))

        assert secrets["KEY1"] == "value1"
        assert secrets["KEY2"] == "value2"
        assert len(secrets) == 2

    def test_parse_quoted_values(self, tmp_path: Path) -> None:
        """Strips double and single quotes from values."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=\"quoted value\"\nKEY2='single quoted'\n")

        provider = VercelSecretsProvider()
        secrets = provider._parse_env_file(str(env_file))

        assert secrets["KEY1"] == "quoted value"
        assert secrets["KEY2"] == "single quoted"

    def test_parse_skips_comments_and_empty_lines(self, tmp_path: Path) -> None:
        """Skips comment lines and empty lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("KEY1=value1\n# comment\n\nKEY2=value2\n")

        provider = VercelSecretsProvider()
        secrets = provider._parse_env_file(str(env_file))

        assert len(secrets) == 2
        assert "KEY1" in secrets
        assert "KEY2" in secrets

    def test_parse_value_with_equals(self, tmp_path: Path) -> None:
        """Handles values containing equals signs."""
        env_file = tmp_path / ".env"
        env_file.write_text("DB_URL=postgres://user:pass@host/db?sslmode=require\n")

        provider = VercelSecretsProvider()
        secrets = provider._parse_env_file(str(env_file))

        assert secrets["DB_URL"] == "postgres://user:pass@host/db?sslmode=require"

    def test_parse_missing_file_raises(self, tmp_path: Path) -> None:
        """Raises RuntimeError for missing file."""
        provider = VercelSecretsProvider()
        with pytest.raises(RuntimeError, match="Env file not found"):
            provider._parse_env_file(str(tmp_path / "nonexistent"))


class TestFlyParseEnvFile:
    """Tests for Fly provider env file parsing."""

    def test_parse_basic_env_file(self, tmp_path: Path) -> None:
        """Parses simple KEY=value lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("DB_URL=postgres://localhost\nSECRET=my_secret\n")

        provider = FlySecretsProvider.__new__(FlySecretsProvider)
        provider._app_name = "test-app"
        provider._fly_cmd = "fly"
        secrets = provider._parse_env_file(str(env_file))

        assert secrets["DB_URL"] == "postgres://localhost"
        assert secrets["SECRET"] == "my_secret"

    def test_parse_quoted_values(self, tmp_path: Path) -> None:
        """Strips quotes from values."""
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET='my secret'\nKEY=\"another value\"\n")

        provider = FlySecretsProvider.__new__(FlySecretsProvider)
        provider._app_name = "test-app"
        provider._fly_cmd = "fly"
        secrets = provider._parse_env_file(str(env_file))

        assert secrets["SECRET"] == "my secret"
        assert secrets["KEY"] == "another value"

    def test_parse_skips_comments(self, tmp_path: Path) -> None:
        """Skips comment lines."""
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nKEY=value\n")

        provider = FlySecretsProvider.__new__(FlySecretsProvider)
        provider._app_name = "test-app"
        provider._fly_cmd = "fly"
        secrets = provider._parse_env_file(str(env_file))

        assert len(secrets) == 1
        assert secrets["KEY"] == "value"

    def test_parse_missing_file_raises(self, tmp_path: Path) -> None:
        """Raises RuntimeError for missing file."""
        provider = FlySecretsProvider.__new__(FlySecretsProvider)
        provider._app_name = "test-app"
        provider._fly_cmd = "fly"

        with pytest.raises(RuntimeError, match="Env file not found"):
            provider._parse_env_file(str(tmp_path / "nonexistent"))


class TestVercelProviderProperties:
    """Tests for Vercel provider initialization and properties."""

    def test_name_is_vercel(self) -> None:
        provider = VercelSecretsProvider()
        assert provider.name == "vercel"

    def test_project_id_stored(self) -> None:
        provider = VercelSecretsProvider(project_id="prj_123")
        assert provider._project_id == "prj_123"

    def test_authenticate_when_cli_missing(self) -> None:
        """Returns False when vercel CLI is not found."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            provider = VercelSecretsProvider()
            assert provider.authenticate() is False


class TestFlyProviderProperties:
    """Tests for Fly provider initialization and properties."""

    def test_name_is_fly(self) -> None:
        provider = FlySecretsProvider.__new__(FlySecretsProvider)
        provider._app_name = "test"
        provider._fly_cmd = "fly"
        assert provider.name == "fly"

    def test_list_secrets_requires_app_name(self) -> None:
        """Raises RuntimeError when no app name is set."""
        provider = FlySecretsProvider.__new__(FlySecretsProvider)
        provider._app_name = None
        provider._fly_cmd = "fly"

        with pytest.raises(RuntimeError, match="App name not configured"):
            provider.list_secrets()

    def test_set_secret_requires_app_name(self) -> None:
        """Raises RuntimeError when no app name is set."""
        provider = FlySecretsProvider.__new__(FlySecretsProvider)
        provider._app_name = None
        provider._fly_cmd = "fly"

        with pytest.raises(RuntimeError, match="App name not configured"):
            provider.set_secret("KEY", "value", "production")

    def test_delete_secret_requires_app_name(self) -> None:
        """Raises RuntimeError when no app name is set."""
        provider = FlySecretsProvider.__new__(FlySecretsProvider)
        provider._app_name = None
        provider._fly_cmd = "fly"

        with pytest.raises(RuntimeError, match="App name not configured"):
            provider.delete_secret("KEY", "production")


class TestGitHubProviderProperties:
    """Tests for GitHub provider initialization and properties."""

    def test_name_is_github(self) -> None:
        provider = GitHubSecretsProvider()
        assert provider.name == "github"

    def test_owner_repo_stored(self) -> None:
        provider = GitHubSecretsProvider(owner="test-org", repo="test-repo")
        assert provider._owner == "test-org"
        assert provider._repo == "test-repo"

    def test_list_secrets_no_owner_returns_empty(self) -> None:
        """Returns empty list when owner/repo not configured."""
        provider = GitHubSecretsProvider()
        assert provider.list_secrets() == []

    def test_set_secret_no_owner_returns_false(self) -> None:
        """Returns False when owner/repo not configured."""
        provider = GitHubSecretsProvider()
        assert provider.set_secret("KEY", "value", "repository") is False

    def test_delete_secret_no_owner_returns_false(self) -> None:
        """Returns False when owner/repo not configured."""
        provider = GitHubSecretsProvider()
        assert provider.delete_secret("KEY", "repository") is False


class TestSecretDataclass:
    """Tests for the Secret dataclass."""

    def test_secret_creation(self) -> None:
        secret = Secret(name="KEY", value="val", environment="production", provider="vercel")
        assert secret.name == "KEY"
        assert secret.value == "val"
        assert secret.environment == "production"
        assert secret.provider == "vercel"

    def test_secret_none_value(self) -> None:
        secret = Secret(name="KEY", value=None, environment="production", provider="github")
        assert secret.value is None


class TestAllowlistValidation:
    """Tests for allowlist validation."""

    def test_validate_no_allowlist_file(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """No allowlist file is considered valid."""
        monkeypatch.chdir(tmp_path)
        # Patch load_config so get_allowlist_path returns a path in tmp_path
        with patch(
            "lib.vibe.secrets.allowlist.load_config",
            return_value={
                "secrets": {"allowlist_path": str(tmp_path / ".vibe" / "secrets.allowlist.json")}
            },
        ):
            valid, issues = validate_allowlist()
        assert valid is True
        assert issues == []

    def test_validate_valid_allowlist(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        """Valid allowlist passes validation."""
        allowlist_file = tmp_path / "allowlist.json"
        data = {"entries": [{"pattern": "test-key", "reason": "Test key", "added_by": "test"}]}
        allowlist_file.write_text(json.dumps(data))

        with patch("lib.vibe.secrets.allowlist.get_allowlist_path", return_value=allowlist_file):
            valid, issues = validate_allowlist()
        assert valid is True
        assert issues == []

    def test_validate_missing_reason(self, tmp_path: Path) -> None:
        """Entry missing reason fails validation."""
        allowlist_file = tmp_path / "allowlist.json"
        data = {"entries": [{"pattern": "test-key", "added_by": "test"}]}
        allowlist_file.write_text(json.dumps(data))

        with patch("lib.vibe.secrets.allowlist.get_allowlist_path", return_value=allowlist_file):
            valid, issues = validate_allowlist()
        assert valid is False
        assert any("reason" in issue for issue in issues)

    def test_validate_invalid_json(self, tmp_path: Path) -> None:
        """Invalid JSON fails validation."""
        allowlist_file = tmp_path / "allowlist.json"
        allowlist_file.write_text("not json")

        with patch("lib.vibe.secrets.allowlist.get_allowlist_path", return_value=allowlist_file):
            valid, issues = validate_allowlist()
        assert valid is False
        assert any("Invalid JSON" in issue for issue in issues)

    def test_validate_missing_entries_key(self, tmp_path: Path) -> None:
        """Missing 'entries' key fails validation."""
        allowlist_file = tmp_path / "allowlist.json"
        allowlist_file.write_text(json.dumps({"other": "data"}))

        with patch("lib.vibe.secrets.allowlist.get_allowlist_path", return_value=allowlist_file):
            valid, issues = validate_allowlist()
        assert valid is False
        assert any("entries" in issue for issue in issues)


class TestAllowlistEntry:
    """Tests for AllowlistEntry dataclass."""

    def test_entry_creation(self) -> None:
        entry = AllowlistEntry(
            pattern="test_*",
            reason="Test keys",
            added_by="developer",
            file_path=".env.test",
            hash="abc123",
        )
        assert entry.pattern == "test_*"
        assert entry.reason == "Test keys"
        assert entry.added_by == "developer"
        assert entry.file_path == ".env.test"
        assert entry.hash == "abc123"

    def test_entry_optional_fields(self) -> None:
        entry = AllowlistEntry(
            pattern="test",
            reason="Test",
            added_by="dev",
        )
        assert entry.file_path is None
        assert entry.hash is None
