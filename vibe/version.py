"""Version management for the Vibe package."""

from importlib import metadata
from pathlib import Path

DIST_NAME = "vibe"
VERSION_FILE = Path(__file__).resolve().parent.parent / "VERSION"


def get_version() -> str:
    """Return the package version from a checkout or installed wheel."""

    try:
        return VERSION_FILE.read_text().strip()
    except FileNotFoundError:
        pass

    try:
        return metadata.version(DIST_NAME)
    except metadata.PackageNotFoundError:
        return "0.0.0-dev"


def bump_version(version: str, bump_type: str) -> str:
    """Bump a semver version string. bump_type is 'patch', 'minor', or 'major'."""

    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid semver: {version}")
    try:
        major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError(f"Invalid semver: {version}")
    if bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    return f"{major}.{minor}.{patch}"


def write_version(new_version: str) -> None:
    """Write version to VERSION file."""

    VERSION_FILE.write_text(new_version + "\n")
