"""Doctor: Validate project configuration and health."""

import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from lib.vibe.config import config_exists, load_config
from lib.vibe.secrets.allowlist import validate_allowlist
from lib.vibe.state import set_last_doctor_run
from lib.vibe.wizards.github import check_gh_cli_auth


class Status(Enum):
    """Check status."""

    PASS = "✓"
    WARN = "⚠"
    FAIL = "✗"
    SKIP = "○"


@dataclass
class CheckResult:
    """Result of a health check."""

    name: str
    status: Status
    message: str
    fix_hint: str | None = None


def run_doctor(verbose: bool = False) -> list[CheckResult]:
    """
    Run all health checks.

    Args:
        verbose: Show additional details

    Returns:
        List of check results
    """
    results = []

    # Core checks
    results.append(check_config_exists())
    results.append(check_gitignore())
    results.append(check_python_version())

    # Tool checks
    results.append(check_git())
    results.append(check_gh_cli())

    # Config-dependent checks
    if config_exists():
        config = load_config()
        results.append(check_tracker_config(config))
        results.append(check_github_config(config))
        results.append(check_secrets_allowlist())

    # Update last run time
    set_last_doctor_run()

    return results


def check_config_exists() -> CheckResult:
    """Check if .vibe/config.json exists."""
    if config_exists():
        return CheckResult(
            name="Config file",
            status=Status.PASS,
            message=".vibe/config.json exists",
        )
    return CheckResult(
        name="Config file",
        status=Status.FAIL,
        message=".vibe/config.json not found",
        fix_hint="Run 'bin/vibe setup' to create configuration",
    )


def check_gitignore() -> CheckResult:
    """Check if .gitignore has required entries."""
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        return CheckResult(
            name="Gitignore",
            status=Status.FAIL,
            message=".gitignore not found",
            fix_hint="Create .gitignore with required entries",
        )

    content = gitignore.read_text()
    required = [".vibe/local_state.json", ".env.local", ".env"]

    missing = [entry for entry in required if entry not in content]

    if missing:
        return CheckResult(
            name="Gitignore",
            status=Status.WARN,
            message=f"Missing entries: {', '.join(missing)}",
            fix_hint="Add missing entries to .gitignore",
        )

    return CheckResult(
        name="Gitignore",
        status=Status.PASS,
        message="All required entries present",
    )


def check_python_version() -> CheckResult:
    """Check Python version is 3.11+."""
    import sys

    version = sys.version_info
    if version >= (3, 11):
        return CheckResult(
            name="Python version",
            status=Status.PASS,
            message=f"Python {version.major}.{version.minor}",
        )

    return CheckResult(
        name="Python version",
        status=Status.FAIL,
        message=f"Python {version.major}.{version.minor} (need 3.11+)",
        fix_hint="Install Python 3.11 or later",
    )


def check_git() -> CheckResult:
    """Check git is installed and we're in a repo."""
    if not shutil.which("git"):
        return CheckResult(
            name="Git",
            status=Status.FAIL,
            message="git not found",
            fix_hint="Install git",
        )

    result = subprocess.run(
        ["git", "rev-parse", "--git-dir"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return CheckResult(
            name="Git",
            status=Status.FAIL,
            message="Not a git repository",
            fix_hint="Run 'git init' or clone a repository",
        )

    return CheckResult(
        name="Git",
        status=Status.PASS,
        message="Git repository detected",
    )


def check_gh_cli() -> CheckResult:
    """Check GitHub CLI is installed and authenticated."""
    if not shutil.which("gh"):
        return CheckResult(
            name="GitHub CLI",
            status=Status.WARN,
            message="gh CLI not installed",
            fix_hint="Install from https://cli.github.com/",
        )

    if check_gh_cli_auth():
        return CheckResult(
            name="GitHub CLI",
            status=Status.PASS,
            message="gh CLI authenticated",
        )

    return CheckResult(
        name="GitHub CLI",
        status=Status.WARN,
        message="gh CLI not authenticated",
        fix_hint="Run 'gh auth login'",
    )


def check_tracker_config(config: dict) -> CheckResult:
    """Check tracker configuration."""
    tracker_type = config.get("tracker", {}).get("type")

    if not tracker_type:
        return CheckResult(
            name="Tracker",
            status=Status.WARN,
            message="No tracker configured",
            fix_hint="Run 'bin/vibe setup' to configure a tracker",
        )

    if tracker_type == "shortcut":
        return CheckResult(
            name="Tracker",
            status=Status.WARN,
            message="Shortcut configured (stub - not functional)",
            fix_hint="See GitHub issue #1 for Shortcut support",
        )

    if tracker_type == "linear":
        import os

        if os.environ.get("LINEAR_API_KEY"):
            return CheckResult(
                name="Tracker",
                status=Status.PASS,
                message="Linear configured with API key",
            )
        return CheckResult(
            name="Tracker",
            status=Status.WARN,
            message="Linear configured but LINEAR_API_KEY not set",
            fix_hint="Add LINEAR_API_KEY to .env.local",
        )

    return CheckResult(
        name="Tracker",
        status=Status.WARN,
        message=f"Unknown tracker type: {tracker_type}",
    )


def check_github_config(config: dict) -> CheckResult:
    """Check GitHub configuration."""
    github = config.get("github", {})
    auth_method = github.get("auth_method")
    owner = github.get("owner")
    repo = github.get("repo")

    if not auth_method:
        return CheckResult(
            name="GitHub config",
            status=Status.FAIL,
            message="GitHub not configured",
            fix_hint="Run 'bin/vibe setup' to configure GitHub",
        )

    if not owner or not repo:
        return CheckResult(
            name="GitHub config",
            status=Status.WARN,
            message="GitHub owner/repo not set",
            fix_hint="Set github.owner and github.repo in .vibe/config.json",
        )

    return CheckResult(
        name="GitHub config",
        status=Status.PASS,
        message=f"GitHub: {owner}/{repo} ({auth_method})",
    )


def check_secrets_allowlist() -> CheckResult:
    """Check secrets allowlist is valid."""
    valid, issues = validate_allowlist()

    if valid:
        return CheckResult(
            name="Secrets allowlist",
            status=Status.PASS,
            message="Allowlist is valid",
        )

    return CheckResult(
        name="Secrets allowlist",
        status=Status.WARN,
        message=f"Allowlist issues: {', '.join(issues)}",
        fix_hint="Fix issues in .vibe/secrets.allowlist.json",
    )


def print_results(results: list[CheckResult]) -> int:
    """
    Print check results and return exit code.

    Returns:
        0 if all pass, 1 if any failures
    """
    print("\n" + "=" * 50)
    print("  Vibe Doctor - Health Check")
    print("=" * 50 + "\n")

    has_failure = False

    for result in results:
        status_char = result.status.value
        print(f"  {status_char} {result.name}: {result.message}")

        if result.fix_hint and result.status in (Status.FAIL, Status.WARN):
            print(f"      → {result.fix_hint}")

        if result.status == Status.FAIL:
            has_failure = True

    print()

    passed = sum(1 for r in results if r.status == Status.PASS)
    total = len(results)
    print(f"  {passed}/{total} checks passed")
    print()

    return 1 if has_failure else 0


if __name__ == "__main__":
    import sys

    results = run_doctor()
    sys.exit(print_results(results))
