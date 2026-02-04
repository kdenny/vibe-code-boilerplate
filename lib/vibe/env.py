"""Environment variable loading utilities."""

import os
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
