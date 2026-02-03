"""Tests for development tools detection and validation."""

from unittest.mock import MagicMock, patch

from lib.vibe.tools import (
    TOOL_DEFINITIONS,
    ToolInfo,
    ToolStatus,
    check_auth,
    check_required_tools,
    check_tool,
    find_command,
    get_install_hint,
    get_platform,
    get_version,
    is_interactive,
    require_interactive,
    require_tool,
)


class TestToolStatusEnum:
    """Tests for ToolStatus enum."""

    def test_status_values(self) -> None:
        assert ToolStatus.INSTALLED.value == "installed"
        assert ToolStatus.AUTHENTICATED.value == "authenticated"
        assert ToolStatus.NOT_INSTALLED.value == "not_installed"
        assert ToolStatus.NOT_AUTHENTICATED.value == "not_authenticated"
        assert ToolStatus.ERROR.value == "error"


class TestToolInfoDataclass:
    """Tests for ToolInfo dataclass."""

    def test_tool_info_defaults(self) -> None:
        info = ToolInfo(name="test", status=ToolStatus.INSTALLED)
        assert info.name == "test"
        assert info.status == ToolStatus.INSTALLED
        assert info.version is None
        assert info.message is None

    def test_tool_info_with_all_fields(self) -> None:
        info = ToolInfo(
            name="git", status=ToolStatus.INSTALLED, version="2.40.0", message="All good"
        )
        assert info.name == "git"
        assert info.version == "2.40.0"
        assert info.message == "All good"


class TestGetPlatform:
    """Tests for get_platform function."""

    def test_get_platform_darwin(self) -> None:
        with patch("lib.vibe.tools.platform.system", return_value="Darwin"):
            assert get_platform() == "macos"

    def test_get_platform_linux(self) -> None:
        with patch("lib.vibe.tools.platform.system", return_value="Linux"):
            assert get_platform() == "linux"

    def test_get_platform_windows(self) -> None:
        with patch("lib.vibe.tools.platform.system", return_value="Windows"):
            assert get_platform() == "windows"

    def test_get_platform_unknown(self) -> None:
        with patch("lib.vibe.tools.platform.system", return_value="FreeBSD"):
            assert get_platform() == "freebsd"


class TestFindCommand:
    """Tests for find_command function."""

    def test_find_command_first_available(self) -> None:
        with patch("lib.vibe.tools.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/python3" if cmd == "python3" else None
            result = find_command(["python3", "python"])
        assert result == "python3"

    def test_find_command_second_available(self) -> None:
        with patch("lib.vibe.tools.shutil.which") as mock_which:
            mock_which.side_effect = lambda cmd: "/usr/bin/python" if cmd == "python" else None
            result = find_command(["python3", "python"])
        assert result == "python"

    def test_find_command_none_available(self) -> None:
        with patch("lib.vibe.tools.shutil.which", return_value=None):
            result = find_command(["nonexistent1", "nonexistent2"])
        assert result is None


class TestGetVersion:
    """Tests for get_version function."""

    def test_get_version_success(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "git version 2.40.0\n"
        mock_result.stderr = ""

        with patch("lib.vibe.tools.subprocess.run", return_value=mock_result):
            version = get_version("git", "--version")

        assert version == "2.40.0"

    def test_get_version_python(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Python 3.12.1\n"
        mock_result.stderr = ""

        with patch("lib.vibe.tools.subprocess.run", return_value=mock_result):
            version = get_version("python3", "--version")

        assert version == "3.12.1"

    def test_get_version_npm(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "npm 10.2.0\n"
        mock_result.stderr = ""

        with patch("lib.vibe.tools.subprocess.run", return_value=mock_result):
            version = get_version("npm", "--version")

        assert version == "10.2.0"

    def test_get_version_with_v_prefix(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "v20.10.0\n"
        mock_result.stderr = ""

        with patch("lib.vibe.tools.subprocess.run", return_value=mock_result):
            version = get_version("node", "--version")

        assert version == "20.10.0"

    def test_get_version_failure(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"

        with patch("lib.vibe.tools.subprocess.run", return_value=mock_result):
            version = get_version("nonexistent", "--version")

        assert version is None

    def test_get_version_exception(self) -> None:
        with patch("lib.vibe.tools.subprocess.run", side_effect=FileNotFoundError()):
            version = get_version("nonexistent", "--version")

        assert version is None


class TestCheckAuth:
    """Tests for check_auth function."""

    def test_check_auth_success(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 0

        with (
            patch("lib.vibe.tools.find_command", return_value="gh"),
            patch("lib.vibe.tools.subprocess.run", return_value=mock_result),
        ):
            result = check_auth(["gh", "auth", "status"])

        assert result is True

    def test_check_auth_failure(self) -> None:
        mock_result = MagicMock()
        mock_result.returncode = 1

        with (
            patch("lib.vibe.tools.find_command", return_value="gh"),
            patch("lib.vibe.tools.subprocess.run", return_value=mock_result),
        ):
            result = check_auth(["gh", "auth", "status"])

        assert result is False

    def test_check_auth_command_not_found(self) -> None:
        with patch("lib.vibe.tools.find_command", return_value=None):
            result = check_auth(["nonexistent", "auth"])

        assert result is False

    def test_check_auth_exception(self) -> None:
        with (
            patch("lib.vibe.tools.find_command", return_value="gh"),
            patch("lib.vibe.tools.subprocess.run", side_effect=Exception("error")),
        ):
            result = check_auth(["gh", "auth", "status"])

        assert result is False


class TestCheckTool:
    """Tests for check_tool function."""

    def test_check_tool_installed(self) -> None:
        with (
            patch("lib.vibe.tools.find_command", return_value="npm"),
            patch("lib.vibe.tools.get_version", return_value="10.2.0"),
        ):
            info = check_tool("npm")

        assert info.name == "npm"
        assert info.status == ToolStatus.INSTALLED
        assert info.version == "10.2.0"

    def test_check_tool_not_installed(self) -> None:
        with (
            patch("lib.vibe.tools.find_command", return_value=None),
            patch("lib.vibe.tools.get_platform", return_value="macos"),
        ):
            info = check_tool("npm")

        assert info.name == "npm"
        assert info.status == ToolStatus.NOT_INSTALLED
        assert info.message is not None

    def test_check_tool_authenticated(self) -> None:
        with (
            patch("lib.vibe.tools.find_command", return_value="gh"),
            patch("lib.vibe.tools.get_version", return_value="2.40.0"),
            patch("lib.vibe.tools.check_auth", return_value=True),
        ):
            info = check_tool("gh")

        assert info.status == ToolStatus.AUTHENTICATED

    def test_check_tool_not_authenticated(self) -> None:
        with (
            patch("lib.vibe.tools.find_command", return_value="gh"),
            patch("lib.vibe.tools.get_version", return_value="2.40.0"),
            patch("lib.vibe.tools.check_auth", return_value=False),
        ):
            info = check_tool("gh")

        assert info.status == ToolStatus.NOT_AUTHENTICATED
        assert "gh auth login" in info.message

    def test_check_tool_unknown(self) -> None:
        info = check_tool("unknown_tool_xyz")

        assert info.status == ToolStatus.ERROR
        assert "Unknown tool" in info.message


class TestGetInstallHint:
    """Tests for get_install_hint function."""

    def test_get_install_hint_macos(self) -> None:
        with patch("lib.vibe.tools.get_platform", return_value="macos"):
            hint = get_install_hint("gh")

        assert "brew install gh" in hint

    def test_get_install_hint_linux(self) -> None:
        with patch("lib.vibe.tools.get_platform", return_value="linux"):
            hint = get_install_hint("python")

        assert "apt install" in hint or "pyenv" in hint

    def test_get_install_hint_all_platforms(self) -> None:
        with patch("lib.vibe.tools.get_platform", return_value="macos"):
            hint = get_install_hint("vercel")

        assert "npm install -g vercel" in hint

    def test_get_install_hint_unknown_tool(self) -> None:
        hint = get_install_hint("unknown_tool")

        assert "Install unknown_tool" in hint


class TestCheckRequiredTools:
    """Tests for check_required_tools function."""

    def test_check_required_tools_all_ok(self) -> None:
        with patch(
            "lib.vibe.tools.check_tool",
            side_effect=[
                ToolInfo("git", ToolStatus.INSTALLED, "2.40.0"),
                ToolInfo("npm", ToolStatus.INSTALLED, "10.2.0"),
            ],
        ):
            all_ok, results = check_required_tools(["git", "npm"])

        assert all_ok is True
        assert len(results) == 2

    def test_check_required_tools_required_missing(self) -> None:
        with patch(
            "lib.vibe.tools.check_tool",
            side_effect=[
                ToolInfo("git", ToolStatus.NOT_INSTALLED, message="Not found"),
            ],
        ):
            all_ok, results = check_required_tools(["git"])

        assert all_ok is False

    def test_check_required_tools_optional_missing(self) -> None:
        with patch(
            "lib.vibe.tools.check_tool",
            side_effect=[
                ToolInfo("npm", ToolStatus.NOT_INSTALLED, message="Not found"),
            ],
        ):
            all_ok, results = check_required_tools(["npm"])

        # npm is optional, so should still be ok
        assert all_ok is True


class TestRequireTool:
    """Tests for require_tool function."""

    def test_require_tool_installed(self) -> None:
        with patch(
            "lib.vibe.tools.check_tool",
            return_value=ToolInfo("npm", ToolStatus.INSTALLED, "10.2.0"),
        ):
            ok, error = require_tool("npm")

        assert ok is True
        assert error is None

    def test_require_tool_not_installed(self) -> None:
        with patch(
            "lib.vibe.tools.check_tool",
            return_value=ToolInfo(
                "npm", ToolStatus.NOT_INSTALLED, message="Install: brew install node"
            ),
        ):
            ok, error = require_tool("npm")

        assert ok is False
        assert "not installed" in error

    def test_require_tool_with_auth_authenticated(self) -> None:
        with patch(
            "lib.vibe.tools.check_tool",
            return_value=ToolInfo("gh", ToolStatus.AUTHENTICATED, "2.40.0"),
        ):
            ok, error = require_tool("gh", need_auth=True)

        assert ok is True
        assert error is None

    def test_require_tool_with_auth_not_authenticated(self) -> None:
        with patch(
            "lib.vibe.tools.check_tool",
            return_value=ToolInfo(
                "gh", ToolStatus.NOT_AUTHENTICATED, "2.40.0", "Run: gh auth login"
            ),
        ):
            ok, error = require_tool("gh", need_auth=True)

        assert ok is False
        assert "not authenticated" in error

    def test_require_tool_error(self) -> None:
        with patch(
            "lib.vibe.tools.check_tool",
            return_value=ToolInfo("test", ToolStatus.ERROR, message="Some error"),
        ):
            ok, error = require_tool("test")

        assert ok is False
        assert "Error checking" in error


class TestIsInteractive:
    """Tests for is_interactive function."""

    def test_is_interactive_true(self) -> None:
        with (
            patch("lib.vibe.tools.sys.stdin") as mock_stdin,
            patch("lib.vibe.tools.sys.stdout") as mock_stdout,
        ):
            mock_stdin.isatty.return_value = True
            mock_stdout.isatty.return_value = True
            result = is_interactive()

        assert result is True

    def test_is_interactive_false_stdin(self) -> None:
        with (
            patch("lib.vibe.tools.sys.stdin") as mock_stdin,
            patch("lib.vibe.tools.sys.stdout") as mock_stdout,
        ):
            mock_stdin.isatty.return_value = False
            mock_stdout.isatty.return_value = True
            result = is_interactive()

        assert result is False

    def test_is_interactive_false_stdout(self) -> None:
        with (
            patch("lib.vibe.tools.sys.stdin") as mock_stdin,
            patch("lib.vibe.tools.sys.stdout") as mock_stdout,
        ):
            mock_stdin.isatty.return_value = True
            mock_stdout.isatty.return_value = False
            result = is_interactive()

        assert result is False


class TestRequireInteractive:
    """Tests for require_interactive function."""

    def test_require_interactive_true(self) -> None:
        with patch("lib.vibe.tools.is_interactive", return_value=True):
            ok, error = require_interactive("Test")

        assert ok is True
        assert error is None

    def test_require_interactive_false(self) -> None:
        with patch("lib.vibe.tools.is_interactive", return_value=False):
            ok, error = require_interactive("Test")

        assert ok is False
        assert "Test wizard requires an interactive terminal" in error
        assert "CI/headless" in error


class TestToolDefinitions:
    """Tests for TOOL_DEFINITIONS structure."""

    def test_required_tools_have_install_instructions(self) -> None:
        for name, definition in TOOL_DEFINITIONS.items():
            if definition.get("required", False):
                assert "install" in definition, f"{name} missing install instructions"

    def test_tools_with_auth_have_auth_hint(self) -> None:
        for name, definition in TOOL_DEFINITIONS.items():
            if "auth_check" in definition:
                assert "auth_hint" in definition, f"{name} has auth_check but no auth_hint"

    def test_all_tools_have_commands(self) -> None:
        for name, definition in TOOL_DEFINITIONS.items():
            assert "commands" in definition, f"{name} missing commands"
            assert len(definition["commands"]) > 0, f"{name} has empty commands"
