"""Tests for GitHub wizard auto-configuration."""

from unittest.mock import patch

from lib.vibe.wizards.github import try_auto_configure_github


def test_try_auto_configure_github_success_when_gh_auth_and_remote() -> None:
    config = {"github": {"auth_method": None, "owner": "", "repo": ""}}
    with (
        patch("lib.vibe.wizards.github.check_gh_cli_auth", return_value=True),
        patch("lib.vibe.wizards.github._detect_remote", return_value=("myorg", "myrepo")),
    ):
        result = try_auto_configure_github(config)
    assert result is True
    assert config["github"]["auth_method"] == "gh_cli"
    assert config["github"]["owner"] == "myorg"
    assert config["github"]["repo"] == "myrepo"


def test_try_auto_configure_github_fails_when_no_gh_auth() -> None:
    config = {"github": {"auth_method": None, "owner": "", "repo": ""}}
    with patch("lib.vibe.wizards.github.check_gh_cli_auth", return_value=False):
        result = try_auto_configure_github(config)
    assert result is False
    assert config["github"]["owner"] == ""
    assert config["github"]["repo"] == ""


def test_try_auto_configure_github_fails_when_no_remote() -> None:
    config = {"github": {"auth_method": None, "owner": "", "repo": ""}}
    with (
        patch("lib.vibe.wizards.github.check_gh_cli_auth", return_value=True),
        patch("lib.vibe.wizards.github._detect_remote", return_value=(None, None)),
    ):
        result = try_auto_configure_github(config)
    assert result is False
    assert config["github"]["owner"] == ""
    assert config["github"]["repo"] == ""
