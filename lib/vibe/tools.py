"""Development tools detection and validation."""

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum


class ToolStatus(Enum):
    """Tool installation/auth status."""

    INSTALLED = "installed"
    AUTHENTICATED = "authenticated"
    NOT_INSTALLED = "not_installed"
    NOT_AUTHENTICATED = "not_authenticated"
    ERROR = "error"


@dataclass
class ToolInfo:
    """Information about a development tool."""

    name: str
    status: ToolStatus
    version: str | None = None
    message: str | None = None


# Platform detection
def get_platform() -> str:
    """Get the current platform (macos, linux, windows)."""
    system = platform.system().lower()
    if system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    return system


# Tool definitions with install instructions per platform
TOOL_DEFINITIONS = {
    "git": {
        "commands": ["git"],
        "version_flag": "--version",
        "required": True,
        "description": "Version control",
        "install": {
            "macos": "xcode-select --install",
            "linux": "sudo apt install git  # or: sudo yum install git",
            "windows": "Download from https://git-scm.com/download/win",
        },
    },
    "python": {
        "commands": ["python3", "python"],
        "version_flag": "--version",
        "required": True,
        "min_version": (3, 11),
        "description": "Python runtime",
        "install": {
            "macos": "brew install python@3.12",
            "linux": "sudo apt install python3.12  # or use pyenv",
            "windows": "Download from https://python.org/downloads/",
        },
    },
    "gh": {
        "commands": ["gh"],
        "version_flag": "--version",
        "auth_check": ["gh", "auth", "status"],
        "required": False,
        "description": "GitHub CLI",
        "install": {
            "macos": "brew install gh",
            "linux": "See https://cli.github.com/",
            "windows": "winget install GitHub.cli",
        },
        "auth_hint": "gh auth login",
    },
    "npm": {
        "commands": ["npm"],
        "version_flag": "--version",
        "required": False,
        "description": "Node.js package manager",
        "install": {
            "macos": "brew install node",
            "linux": "See https://nodejs.org/",
            "windows": "Download from https://nodejs.org/",
        },
    },
    "fly": {
        "commands": ["fly", "flyctl"],
        "version_flag": "version",
        "auth_check": ["fly", "auth", "whoami"],
        "required": False,
        "description": "Fly.io CLI",
        "install": {
            "macos": "brew install flyctl",
            "linux": "curl -L https://fly.io/install.sh | sh",
            "windows": 'powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"',
        },
        "auth_hint": "fly auth login",
    },
    "vercel": {
        "commands": ["vercel"],
        "version_flag": "--version",
        "auth_check": ["vercel", "whoami"],
        "required": False,
        "description": "Vercel CLI",
        "install": {
            "all": "npm install -g vercel",
        },
        "auth_hint": "vercel login",
    },
    "supabase": {
        "commands": ["supabase"],
        "version_flag": "--version",
        "required": False,
        "description": "Supabase CLI",
        "install": {
            "macos": "brew install supabase/tap/supabase",
            "linux": "brew install supabase/tap/supabase  # or: npm install -g supabase",
            "windows": "npm install -g supabase",
        },
        "auth_hint": "supabase login",
    },
    "neonctl": {
        "commands": ["neonctl"],
        "version_flag": "--version",
        "required": False,
        "description": "Neon database CLI",
        "install": {
            "all": "npm install -g neonctl",
        },
        "auth_hint": "neonctl auth",
    },
}


def find_command(commands: list[str]) -> str | None:
    """Find the first available command from a list of alternatives."""
    for cmd in commands:
        if shutil.which(cmd):
            return cmd
    return None


def get_version(command: str, version_flag: str) -> str | None:
    """Get version string from a command."""
    try:
        result = subprocess.run(
            [command, version_flag],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            # Extract first line, clean up common prefixes
            output = result.stdout.strip() or result.stderr.strip()
            first_line = output.split("\n")[0]
            # Remove common prefixes like "git version ", "Python ", etc.
            for prefix in ["git version ", "Python ", "npm ", "v"]:
                if first_line.startswith(prefix):
                    first_line = first_line[len(prefix) :]
            return first_line.split()[0] if first_line else None
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass
    return None


def check_auth(auth_command: list[str]) -> bool:
    """Check if a tool is authenticated."""
    try:
        # Use the actual command that's available
        cmd = find_command([auth_command[0]])
        if not cmd:
            return False
        actual_command = [cmd] + auth_command[1:]
        result = subprocess.run(
            actual_command,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def check_tool(tool_name: str) -> ToolInfo:
    """
    Check if a tool is installed and optionally authenticated.

    Args:
        tool_name: Name of the tool to check (must be in TOOL_DEFINITIONS)

    Returns:
        ToolInfo with status, version, and any messages
    """
    if tool_name not in TOOL_DEFINITIONS:
        return ToolInfo(
            name=tool_name,
            status=ToolStatus.ERROR,
            message=f"Unknown tool: {tool_name}",
        )

    definition = TOOL_DEFINITIONS[tool_name]
    commands = definition["commands"]
    version_flag = definition.get("version_flag", "--version")

    # Find the command
    cmd = find_command(commands)
    if not cmd:
        return ToolInfo(
            name=tool_name,
            status=ToolStatus.NOT_INSTALLED,
            message=get_install_hint(tool_name),
        )

    # Get version
    version = get_version(cmd, version_flag)

    # Check authentication if applicable
    auth_check = definition.get("auth_check")
    if auth_check:
        if check_auth(auth_check):
            return ToolInfo(
                name=tool_name,
                status=ToolStatus.AUTHENTICATED,
                version=version,
            )
        else:
            auth_hint = definition.get("auth_hint", "")
            return ToolInfo(
                name=tool_name,
                status=ToolStatus.NOT_AUTHENTICATED,
                version=version,
                message=f"Run: {auth_hint}" if auth_hint else "Not authenticated",
            )

    return ToolInfo(
        name=tool_name,
        status=ToolStatus.INSTALLED,
        version=version,
    )


def get_install_hint(tool_name: str) -> str:
    """Get platform-specific install instructions for a tool."""
    if tool_name not in TOOL_DEFINITIONS:
        return f"Install {tool_name}"

    definition = TOOL_DEFINITIONS[tool_name]
    install = definition.get("install", {})
    current_platform = get_platform()

    # Check for platform-specific or 'all' instruction
    if "all" in install:
        return f"Install: {install['all']}"
    elif current_platform in install:
        return f"Install: {install[current_platform]}"
    else:
        # Return first available
        for plat, cmd in install.items():
            return f"Install ({plat}): {cmd}"

    return f"Install {tool_name}"


def check_required_tools(tool_names: list[str]) -> tuple[bool, list[ToolInfo]]:
    """
    Check multiple tools and return results.

    Args:
        tool_names: List of tool names to check

    Returns:
        Tuple of (all_ok, list of ToolInfo)
    """
    results = []
    all_ok = True

    for name in tool_names:
        info = check_tool(name)
        results.append(info)

        # Check if this is a required tool that's missing
        definition = TOOL_DEFINITIONS.get(name, {})
        if definition.get("required", False):
            if info.status in (ToolStatus.NOT_INSTALLED, ToolStatus.ERROR):
                all_ok = False

    return all_ok, results


def require_tool(tool_name: str, need_auth: bool = False) -> tuple[bool, str | None]:
    """
    Check that a tool is available (and optionally authenticated).

    Use this at the start of wizards to validate prerequisites.

    Args:
        tool_name: Name of the tool to check
        need_auth: Whether authentication is required

    Returns:
        Tuple of (success, error_message or None)
    """
    info = check_tool(tool_name)

    if info.status == ToolStatus.NOT_INSTALLED:
        return False, f"{tool_name} is not installed. {info.message}"

    if info.status == ToolStatus.ERROR:
        return False, f"Error checking {tool_name}: {info.message}"

    if need_auth and info.status == ToolStatus.NOT_AUTHENTICATED:
        return False, f"{tool_name} is not authenticated. {info.message}"

    return True, None


def is_interactive() -> bool:
    """Check if we're running in an interactive terminal."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def require_interactive(wizard_name: str) -> tuple[bool, str | None]:
    """
    Check that we're in an interactive terminal.

    Use this at the start of wizards that need user input.

    Args:
        wizard_name: Name of the wizard (for error message)

    Returns:
        Tuple of (success, error_message or None)
    """
    if is_interactive():
        return True, None

    return False, (
        f"The {wizard_name} wizard requires an interactive terminal.\n"
        "For CI/headless environments, configure via:\n"
        "  - Environment variables\n"
        "  - .vibe/config.json\n"
        "  - CLI flags (where available)"
    )


# =============================================================================
# Input Validation
# =============================================================================

import re


def validate_github_owner(value: str) -> tuple[bool, str]:
    """
    Validate GitHub owner (user or org) name.

    Returns:
        (is_valid, error_message)
    """
    if not value:
        return False, "Owner cannot be empty"
    if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$", value):
        return False, "Owner must be alphanumeric with optional hyphens (not at start/end)"
    if len(value) > 39:
        return False, "Owner must be 39 characters or less"
    return True, ""


def validate_github_repo(value: str) -> tuple[bool, str]:
    """
    Validate GitHub repository name.

    Returns:
        (is_valid, error_message)
    """
    if not value:
        return False, "Repository name cannot be empty"
    if not re.match(r"^[a-zA-Z0-9._-]+$", value):
        return False, "Repository name can only contain alphanumeric, dots, hyphens, underscores"
    if value.startswith("."):
        return False, "Repository name cannot start with a dot"
    if len(value) > 100:
        return False, "Repository name must be 100 characters or less"
    return True, ""


def validate_branch_pattern(pattern: str) -> tuple[bool, str]:
    """
    Validate branch naming pattern.

    Returns:
        (is_valid, error_message)
    """
    if not pattern:
        return False, "Branch pattern cannot be empty"
    if "{PROJ}" not in pattern and "{num}" not in pattern:
        return False, "Pattern must contain {PROJ} or {num} placeholder"
    return True, ""


def validate_linear_team_id(value: str) -> tuple[bool, str]:
    """
    Validate Linear team ID format.

    Linear team IDs are UUIDs or short IDs.

    Returns:
        (is_valid, error_message)
    """
    if not value:
        return True, ""  # Optional field

    # UUID format
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    if re.match(uuid_pattern, value.lower()):
        return True, ""

    # Short ID format (alphanumeric)
    if re.match(r"^[a-zA-Z0-9_-]+$", value) and len(value) <= 50:
        return True, ""

    return False, "Team ID should be a UUID or alphanumeric identifier"


# =============================================================================
# Git Helpers
# =============================================================================


def get_default_branch() -> str:
    """
    Get the default branch name (main or master).

    Returns:
        Branch name, defaults to "main" if detection fails
    """
    # Try to get from remote HEAD
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            # Output is like "refs/remotes/origin/main"
            return result.stdout.strip().split("/")[-1]
    except Exception:
        pass

    # Try to check if main exists
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "origin/main"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "main"
    except Exception:
        pass

    # Check for master
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", "origin/master"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "master"
    except Exception:
        pass

    # Default to main
    return "main"


# =============================================================================
# Doctor Helpers
# =============================================================================


def print_tool_status(tool_names: list[str]) -> None:
    """Print a formatted status of tools (for doctor command)."""
    import click

    for name in tool_names:
        info = check_tool(name)
        definition = TOOL_DEFINITIONS.get(name, {})
        description = definition.get("description", name)

        if info.status == ToolStatus.AUTHENTICATED:
            version_str = f" ({info.version})" if info.version else ""
            click.echo(f"  \u2713 {description}: authenticated{version_str}")
        elif info.status == ToolStatus.INSTALLED:
            version_str = f" ({info.version})" if info.version else ""
            click.echo(f"  \u2713 {description}: installed{version_str}")
        elif info.status == ToolStatus.NOT_AUTHENTICATED:
            version_str = f" ({info.version})" if info.version else ""
            click.echo(f"  \u26a0 {description}: not authenticated{version_str}")
            if info.message:
                click.echo(f"      \u2192 {info.message}")
        elif info.status == ToolStatus.NOT_INSTALLED:
            required = definition.get("required", False)
            marker = "\u2717" if required else "\u25cb"
            suffix = "" if required else " (optional)"
            click.echo(f"  {marker} {description}: not installed{suffix}")
            if info.message:
                click.echo(f"      \u2192 {info.message}")
        else:
            click.echo(f"  ? {description}: {info.message}")
