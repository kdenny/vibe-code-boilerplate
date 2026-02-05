"""Tests for UI validation module."""

import os
from unittest.mock import MagicMock, patch

import pytest

from lib.vibe.ui.validation import SetupValidator, ValidationResult, print_validation_results


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
    def test_authenticated_with_repo(self, mock_run: MagicMock, mock_which: MagicMock) -> None:
        mock_which.return_value = "/usr/bin/gh"
        # First call: auth status, second call: repo view
        mock_run.side_effect = [
            MagicMock(returncode=0),
            MagicMock(returncode=0),
        ]
        config = {"github": {"auth_method": "gh_cli", "owner": "me", "repo": "test"}}
        validator = SetupValidator(config)
        result = validator.validate_github()
        assert result.success is True
        assert "me/test" in result.message


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
    def test_valid_api_key(self, mock_urlopen: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        config = {"tracker": {"type": "linear"}}
        validator = SetupValidator(config)
        result = validator.validate_linear()
        assert result.success is True
        assert "valid" in result.message.lower()


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
