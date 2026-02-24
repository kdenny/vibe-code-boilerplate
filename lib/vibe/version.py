"""Version management for vibe-code-boilerplate."""

from pathlib import Path


def get_version() -> str:
    """Read version from VERSION file."""
    version_file = Path(__file__).parent.parent.parent / "VERSION"
    return version_file.read_text().strip()


def bump_version(version: str, bump_type: str) -> str:
    """Bump a semver version string. bump_type is 'patch' or 'minor'."""
    parts = version.split(".")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    return f"{major}.{minor}.{patch}"


def write_version(new_version: str) -> None:
    """Write version to VERSION file."""
    version_file = Path(__file__).parent.parent.parent / "VERSION"
    version_file.write_text(new_version + "\n")
