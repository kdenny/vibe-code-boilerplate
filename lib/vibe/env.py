"""Environment variable loading utilities."""

import os
import shutil
import subprocess
from pathlib import Path


def load_env_files(
    project_root: Path | None = None,
    environment: str | None = None,
    verbose: bool = False,
) -> list[str]:
    """
    Load environment variables from .env files.

    Load order (later files override earlier):
    1. .env - Base/default values
    2. .env.local - Local overrides (gitignored)
    3. .env.{environment} - Environment-specific (e.g., .env.development)
    4. .env.{environment}.local - Local environment overrides

    Args:
        project_root: Project root directory (defaults to cwd)
        environment: Environment name (e.g., 'development', 'production')
        verbose: Print loaded files

    Returns:
        List of loaded file paths
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        # python-dotenv not installed, skip env loading
        if verbose:
            print("Note: python-dotenv not installed, skipping .env loading")
        return []

    root = project_root or Path.cwd()
    loaded: list[str] = []

    # Build list of env files in load order
    env_files: list[Path] = [
        root / ".env",
        root / ".env.local",
    ]

    if environment:
        env_files.extend(
            [
                root / f".env.{environment}",
                root / f".env.{environment}.local",
            ]
        )

    # Load each file if it exists
    for env_file in env_files:
        if env_file.exists():
            load_dotenv(env_file, override=True)
            loaded.append(str(env_file))
            if verbose:
                print(f"Loaded: {env_file}")

    return loaded


def get_environment() -> str | None:
    """
    Get the current environment name from common env vars.

    Checks in order:
    - VIBE_ENV
    - NODE_ENV
    - ENVIRONMENT
    - ENV
    """
    for var in ["VIBE_ENV", "NODE_ENV", "ENVIRONMENT", "ENV"]:
        value = os.environ.get(var)
        if value:
            return value.lower()
    return None


def auto_load_env(verbose: bool = False) -> list[str]:
    """
    Automatically load environment variables from .env files.

    This is the main entry point called at CLI startup.
    Uses get_environment() to determine environment-specific files to load.

    Args:
        verbose: Print loaded files

    Returns:
        List of loaded file paths
    """
    environment = get_environment()
    return load_env_files(environment=environment, verbose=verbose)


def setup_direnv(project_root: Path | None = None) -> dict[str, bool]:
    """
    Set up direnv for automatic env variable loading.

    Creates a .envrc file, adds .envrc and .direnv/ to .gitignore,
    and runs `direnv allow` if direnv is installed.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Dict with keys: envrc_created, gitignore_updated, direnv_allowed
    """
    root = project_root or Path.cwd()
    result = {"envrc_created": False, "gitignore_updated": False, "direnv_allowed": False}

    # Create .envrc
    envrc_path = root / ".envrc"
    if not envrc_path.exists():
        envrc_path.write_text("dotenv_if_exists .env.local\n", encoding="utf-8")
        result["envrc_created"] = True

    # Add .envrc and .direnv/ to .gitignore if not already there
    gitignore_path = root / ".gitignore"
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding="utf-8")
        additions = []
        if ".envrc" not in content:
            additions.append(".envrc")
        if ".direnv/" not in content:
            additions.append(".direnv/")
        if additions:
            # Add under the existing "Environment files" section if present,
            # otherwise append at the end
            new_entries = "\n".join(additions)
            if not content.endswith("\n"):
                content += "\n"
            content += new_entries + "\n"
            gitignore_path.write_text(content, encoding="utf-8")
            result["gitignore_updated"] = True

    # Run direnv allow if direnv is installed
    if shutil.which("direnv"):
        try:
            subprocess.run(
                ["direnv", "allow", str(root)],
                capture_output=True,
                text=True,
                cwd=str(root),
            )
            result["direnv_allowed"] = True
        except (subprocess.CalledProcessError, OSError):
            pass

    return result


def check_direnv_status(project_root: Path | None = None) -> dict[str, bool | str | None]:
    """
    Check direnv configuration status for doctor checks.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Dict with keys:
            envrc_exists: bool - whether .envrc file exists
            direnv_installed: bool - whether direnv binary is available
            direnv_allowed: bool | None - whether direnv has allowed this dir
                (None if direnv not installed or .envrc doesn't exist)
    """
    root = project_root or Path.cwd()
    status: dict[str, bool | str | None] = {
        "envrc_exists": False,
        "direnv_installed": False,
        "direnv_allowed": None,
    }

    envrc_path = root / ".envrc"
    status["envrc_exists"] = envrc_path.exists()
    status["direnv_installed"] = shutil.which("direnv") is not None

    if status["envrc_exists"] and status["direnv_installed"]:
        try:
            result = subprocess.run(
                ["direnv", "status"],
                capture_output=True,
                text=True,
                cwd=str(root),
            )
            # direnv status outputs "Found RC allowed true" when allowed
            output = result.stdout
            if "Found RC allowed true" in output:
                status["direnv_allowed"] = True
            elif "Found RC allowed false" in output:
                status["direnv_allowed"] = False
            else:
                # Could not determine status
                status["direnv_allowed"] = None
        except (subprocess.CalledProcessError, OSError):
            status["direnv_allowed"] = None

    return status
