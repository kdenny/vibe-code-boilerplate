"""Tests for UI validation module."""

import os
import urllib.error
from unittest.mock import MagicMock, patch

from vibe.ui.validation import SetupValidator, ValidationResult, print_validation_results


def _mock_http_response(status: int, body: bytes) -> MagicMock:
    """Build a context-manager mock standing in for urlopen()'s return."""
    response = MagicMock()
    response.status = status
    response.read.return_value = body
    response.__enter__ = MagicMock(return_value=response)
    response.__exit__ = MagicMock(return_value=False)
    return response


class TestValidationResult:
    def test_creation(self) -> None:
        result = ValidationResult(
            name="Test",
            success=True,
            message="All good",
        )
        assert result.name == "Test"
        assert result.success is True
        assert result.message == "All good"
        assert result.details is None
        assert result.optional is False

    def test_creation_with_details(self) -> None:
        result = ValidationResult(
            name="Test",
            success=False,
            message="Failed",
            details="See docs",
        )
        assert result.details == "See docs"


class TestSetupValidator:
    def test_run_all_empty_config(self) -> None:
        config: dict = {}
        validator = SetupValidator(config)
        results = validator.run_all()
        assert results == []  # Nothing configured, nothing to validate

    def test_run_all_with_github(self) -> None:
        config = {"github": {"auth_method": "gh_cli", "owner": "me", "repo": "test"}}
        validator = SetupValidator(config)
        with patch.object(validator, "validate_github") as mock_validate:
            mock_validate.return_value = ValidationResult("GitHub", True, "OK")
            results = validator.run_all()
            mock_validate.assert_called_once()
            assert len(results) == 1

    def test_run_all_with_linear(self) -> None:
        config = {"tracker": {"type": "linear"}}
        validator = SetupValidator(config)
        with patch.object(validator, "validate_linear") as mock_validate:
            mock_validate.return_value = ValidationResult("Linear", True, "OK")
            results = validator.run_all()
            mock_validate.assert_called_once()
            assert len(results) == 1

    def test_run_all_with_shortcut(self) -> None:
        config = {"tracker": {"type": "shortcut"}}
        validator = SetupValidator(config)
        with patch.object(validator, "validate_shortcut") as mock_validate:
            mock_validate.return_value = ValidationResult("Shortcut", True, "OK")
            results = validator.run_all()
            mock_validate.assert_called_once()
            assert len(results) == 1

    def test_run_all_axiom_only_when_enabled(self) -> None:
        # Axiom is optional: not validated unless explicitly enabled.
        validator = SetupValidator({"observability": {"axiom": {"enabled": False}}})
        with patch.object(validator, "validate_axiom") as mock_validate:
            assert validator.run_all() == []
            mock_validate.assert_not_called()

        validator = SetupValidator({"observability": {"axiom": {"enabled": True}}})
        with patch.object(validator, "validate_axiom") as mock_validate:
            mock_validate.return_value = ValidationResult("Axiom", True, "OK", optional=True)
            results = validator.run_all()
            mock_validate.assert_called_once()
            assert len(results) == 1


class TestValidateGitHub:
    @patch("shutil.which")
    def test_no_gh_cli(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None
        config = {"github": {"auth_method": "gh_cli"}}
        validator = SetupValidator(config)
        result = validator.validate_github()
        assert result.success is False
        assert "not installed" in result.message.lower()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_not_authenticated(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/gh"
        mock_run.return_value = MagicMock(returncode=1, stderr="Not logged in")
        config = {"github": {"auth_method": "gh_cli"}}
        validator = SetupValidator(config)
        result = validator.validate_github()
        assert result.success is False
        assert "not authenticated" in result.message.lower()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_authenticated_no_repo(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/gh"
        mock_run.return_value = MagicMock(returncode=0)
        config = {"github": {"auth_method": "gh_cli"}}  # No owner/repo
        validator = SetupValidator(config)
        result = validator.validate_github()
        assert result.success is True
        assert "no repo configured" in result.message.lower()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_authenticated_with_repo_write_access(
        self, mock_run: MagicMock, mock_which: MagicMock
    ) -> None:
        mock_which.return_value = "/usr/bin/gh"
        # First call: auth status, second call: repo view (returns permission).
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0, stdout='{"name": "test", "viewerPermission": "WRITE"}'),
        ]
        config = {"github": {"auth_method": "gh_cli", "owner": "me", "repo": "test"}}
        validator = SetupValidator(config)
        result = validator.validate_github()
        assert result.success is True
        assert "me/test" in result.message
        assert "open PRs" in result.message

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_insufficient_permission(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/gh"
        # Authenticated, repo readable, but only READ access — the pilot cannot
        # open PRs or set labels, so this must fail loudly before the first run.
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0, stdout='{"name": "test", "viewerPermission": "READ"}'),
        ]
        config = {"github": {"auth_method": "gh_cli", "owner": "me", "repo": "test"}}
        validator = SetupValidator(config)
        result = validator.validate_github()
        assert result.success is False
        assert "permission" in result.message.lower()
        assert result.details is not None
        assert "Write" in result.details

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_cannot_access_repo(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/gh"
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=1, stderr="Could not resolve to a Repository"),
        ]
        config = {"github": {"auth_method": "gh_cli", "owner": "me", "repo": "ghost"}}
        validator = SetupValidator(config)
        result = validator.validate_github()
        assert result.success is False
        assert "cannot access" in result.message.lower()


class TestValidateLinear:
    @patch.dict(os.environ, {}, clear=True)
    def test_no_api_key(self) -> None:
        config = {"tracker": {"type": "linear"}}
        validator = SetupValidator(config)
        result = validator.validate_linear()
        assert result.success is False
        assert "not set" in result.message.lower()

    @patch.dict(os.environ, {"LINEAR_API_KEY": "lin_api_test"})
    @patch("urllib.request.urlopen")
    def test_valid_api_key_no_team(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _mock_http_response(200, b"{}")

        config = {"tracker": {"type": "linear"}}
        validator = SetupValidator(config)
        result = validator.validate_linear()
        # Valid key but no team configured: success with an actionable note.
        assert result.success is True
        assert "valid" in result.message.lower()
        assert result.details is not None
        assert "team" in result.details.lower()

    @patch.dict(os.environ, {"LINEAR_API_KEY": "lin_api_test"})
    @patch("urllib.request.urlopen")
    def test_team_reachable(self, mock_urlopen: MagicMock) -> None:
        # First call: viewer ping; second call: team lookup.
        mock_urlopen.side_effect = [
            _mock_http_response(200, b"{}"),
            _mock_http_response(200, b'{"data": {"team": {"id": "t1", "name": "Engineering"}}}'),
        ]
        config = {"tracker": {"type": "linear", "config": {"team_id": "t1"}}}
        validator = SetupValidator(config)
        result = validator.validate_linear()
        assert result.success is True
        assert "Engineering" in result.message
        assert "failure logging ready" in result.message

    @patch.dict(os.environ, {"LINEAR_API_KEY": "lin_api_test"})
    @patch("urllib.request.urlopen")
    def test_team_not_accessible(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = [
            _mock_http_response(200, b"{}"),
            _mock_http_response(200, b'{"data": {"team": null}}'),
        ]
        config = {"tracker": {"type": "linear", "config": {"team_id": "bogus"}}}
        validator = SetupValidator(config)
        result = validator.validate_linear()
        assert result.success is False
        assert "not accessible" in result.message.lower()
        assert result.details is not None
        assert "bogus" in result.details


class TestValidateVercel:
    @patch("shutil.which")
    def test_no_cli(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None
        config = {"deployment": {"vercel": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_vercel()
        assert result.success is False
        assert "not installed" in result.message.lower()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_authenticated(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/vercel"
        mock_run.return_value = MagicMock(returncode=0, stdout="testuser")
        config = {"deployment": {"vercel": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_vercel()
        assert result.success is True
        assert "testuser" in result.message


class TestValidateFly:
    @patch("shutil.which")
    def test_no_cli(self, mock_which: MagicMock) -> None:
        mock_which.return_value = None
        config = {"deployment": {"fly": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_fly()
        assert result.success is False
        assert "not installed" in result.message.lower()

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_authenticated(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.side_effect = lambda cmd: "/usr/bin/fly" if cmd == "fly" else None
        mock_run.return_value = MagicMock(returncode=0, stdout="testuser@example.com")
        config = {"deployment": {"fly": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_fly()
        assert result.success is True


class TestValidateSentry:
    @patch.dict(os.environ, {}, clear=True)
    def test_no_dsn(self) -> None:
        config = {"observability": {"sentry": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_sentry()
        assert result.success is False
        assert "not set" in result.message.lower()

    @patch.dict(os.environ, {"SENTRY_DSN": "invalid"})
    def test_invalid_dsn_format(self) -> None:
        config = {"observability": {"sentry": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_sentry()
        assert result.success is False
        assert "invalid" in result.message.lower()

    @patch.dict(os.environ, {"SENTRY_DSN": "https://key@o123.ingest.sentry.io/456"})
    def test_valid_dsn(self) -> None:
        config = {"observability": {"sentry": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_sentry()
        assert result.success is True


class TestValidateAxiom:
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_env_is_optional(self) -> None:
        config = {"observability": {"axiom": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_axiom()
        assert result.success is False
        assert result.optional is True
        assert "AXIOM_API_TOKEN" in result.message

    @patch.dict(
        os.environ,
        {"AXIOM_API_TOKEN": "xapt-x", "AXIOM_ORG_ID": "org1", "AXIOM_DATASET": "myapp"},
    )
    @patch("urllib.request.urlopen")
    def test_connected(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.return_value = _mock_http_response(200, b'{"tables": []}')
        config = {"observability": {"axiom": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_axiom()
        assert result.success is True
        assert result.optional is True
        assert "myapp" in result.message

    @patch.dict(os.environ, {"AXIOM_API_TOKEN": "xapt-x", "AXIOM_ORG_ID": "org1"})
    @patch("urllib.request.urlopen")
    def test_token_rejected(self, mock_urlopen: MagicMock) -> None:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url",
            401,
            "Unauthorized",
            {},
            None,  # type: ignore[arg-type]
        )
        config = {"observability": {"axiom": {"enabled": True}}}
        validator = SetupValidator(config)
        result = validator.validate_axiom()
        assert result.success is False
        assert result.optional is True
        assert "401" in result.message
        assert result.details is not None and "Token" in result.details


class TestPrintValidationResults:
    @patch("click.echo")
    @patch("click.style")
    def test_print_results(self, mock_style: MagicMock, mock_echo: MagicMock) -> None:
        mock_style.side_effect = lambda text, fg: text  # Just return the text
        results = [
            ValidationResult("Test1", True, "OK"),
            ValidationResult("Test2", False, "Failed", "Fix it"),
        ]
        print_validation_results(results)
        # Should have been called multiple times
        assert mock_echo.call_count > 0
        # Check that pass/fail summary was printed
        calls_str = " ".join(str(call) for call in mock_echo.call_args_list)
        assert "1 passed" in calls_str
        assert "1 failed" in calls_str

    @patch("click.echo")
    @patch("click.style")
    def test_optional_failure_is_warning(self, mock_style: MagicMock, mock_echo: MagicMock) -> None:
        mock_style.side_effect = lambda text, fg: text
        results = [
            ValidationResult("Linear", True, "OK"),
            ValidationResult("Axiom", False, "down", "fix", optional=True),
        ]
        print_validation_results(results)
        calls_str = " ".join(str(call) for call in mock_echo.call_args_list)
        # Optional failure counts as a warning, not a hard failure.
        assert "1 passed, 0 failed" in calls_str
        assert "optional warning" in calls_str
        assert "(optional)" in calls_str
