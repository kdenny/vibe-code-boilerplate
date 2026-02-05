"""Live integration validation for setup wizard."""

import os
import shutil
import subprocess
from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationResult:
    """Result of a validation check."""

    name: str
    success: bool
    message: str
    details: str | None = None


class SetupValidator:
    """Live integration checks for validating setup.

    Performs actual API calls and connectivity checks to verify
    that configured integrations are working.

    Example:
        validator = SetupValidator(config)
        results = validator.run_all()
        for result in results:
            status = "PASS" if result.success else "FAIL"
            print(f"{status}: {result.name} - {result.message}")
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize validator.

        Args:
            config: Current project configuration
        """
        self.config = config

    def run_all(self) -> list[ValidationResult]:
        """Run all applicable validation checks.

        Returns:
            List of ValidationResult objects
        """
        results = []

        # GitHub validation
        if self.config.get("github", {}).get("auth_method"):
            results.append(self.validate_github())

        # Tracker validation
        tracker_type = self.config.get("tracker", {}).get("type")
        if tracker_type == "linear":
            results.append(self.validate_linear())
        elif tracker_type == "shortcut":
            results.append(self.validate_shortcut())

        # Deployment validation
        if self.config.get("deployment", {}).get("vercel", {}).get("enabled"):
            results.append(self.validate_vercel())

        if self.config.get("deployment", {}).get("fly", {}).get("enabled"):
            results.append(self.validate_fly())

        # Database validation
        if self.config.get("database", {}).get("neon", {}).get("enabled"):
            results.append(self.validate_neon())

        if self.config.get("database", {}).get("supabase", {}).get("enabled"):
            results.append(self.validate_supabase())

        # Monitoring validation
        if self.config.get("observability", {}).get("sentry", {}).get("enabled"):
            results.append(self.validate_sentry())

        return results

    def validate_github(self) -> ValidationResult:
        """Validate GitHub CLI authentication and repo access.

        Returns:
            ValidationResult with success status and details
        """
        # Check gh CLI exists
        if not shutil.which("gh"):
            return ValidationResult(
                name="GitHub",
                success=False,
                message="gh CLI not installed",
                details="Install from https://cli.github.com/",
            )

        # Check authentication
        try:
            result = subprocess.run(
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode != 0:
                return ValidationResult(
                    name="GitHub",
                    success=False,
                    message="Not authenticated",
                    details="Run 'gh auth login' to authenticate",
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                name="GitHub",
                success=False,
                message="Authentication check timed out",
            )
        except Exception as e:
            return ValidationResult(
                name="GitHub",
                success=False,
                message=f"Error checking auth: {e}",
            )

        # Check repo access
        owner = self.config.get("github", {}).get("owner")
        repo = self.config.get("github", {}).get("repo")

        if owner and repo:
            try:
                result = subprocess.run(
                    ["gh", "repo", "view", f"{owner}/{repo}", "--json", "name"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    return ValidationResult(
                        name="GitHub",
                        success=True,
                        message=f"Connected to {owner}/{repo}",
                    )
                else:
                    return ValidationResult(
                        name="GitHub",
                        success=False,
                        message=f"Cannot access {owner}/{repo}",
                        details=result.stderr.strip() if result.stderr else None,
                    )
            except subprocess.TimeoutExpired:
                return ValidationResult(
                    name="GitHub",
                    success=False,
                    message="Repo check timed out",
                )

        return ValidationResult(
            name="GitHub",
            success=True,
            message="Authenticated (no repo configured)",
        )

    def validate_linear(self) -> ValidationResult:
        """Validate Linear API key and team access.

        Returns:
            ValidationResult with success status and details
        """
        api_key = os.environ.get("LINEAR_API_KEY")

        if not api_key:
            return ValidationResult(
                name="Linear",
                success=False,
                message="LINEAR_API_KEY not set",
                details="Add to .env.local",
            )

        # Try a simple API call
        try:
            import urllib.request

            req = urllib.request.Request(
                "https://api.linear.app/graphql",
                data=b'{"query": "{ viewer { id name } }"}',
                headers={
                    "Authorization": api_key,
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return ValidationResult(
                        name="Linear",
                        success=True,
                        message="API key valid",
                    )
                else:
                    return ValidationResult(
                        name="Linear",
                        success=False,
                        message=f"API returned {response.status}",
                    )
        except Exception as e:
            return ValidationResult(
                name="Linear",
                success=False,
                message=f"API check failed: {e}",
            )

    def validate_shortcut(self) -> ValidationResult:
        """Validate Shortcut API token.

        Returns:
            ValidationResult with success status and details
        """
        api_token = os.environ.get("SHORTCUT_API_TOKEN")

        if not api_token:
            return ValidationResult(
                name="Shortcut",
                success=False,
                message="SHORTCUT_API_TOKEN not set",
                details="Add to .env.local",
            )

        # Try a simple API call
        try:
            import urllib.request

            req = urllib.request.Request(
                "https://api.app.shortcut.com/api/v3/member",
                headers={
                    "Shortcut-Token": api_token,
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return ValidationResult(
                        name="Shortcut",
                        success=True,
                        message="API token valid",
                    )
                else:
                    return ValidationResult(
                        name="Shortcut",
                        success=False,
                        message=f"API returned {response.status}",
                    )
        except Exception as e:
            return ValidationResult(
                name="Shortcut",
                success=False,
                message=f"API check failed: {e}",
            )

    def validate_vercel(self) -> ValidationResult:
        """Validate Vercel CLI authentication.

        Returns:
            ValidationResult with success status and details
        """
        if not shutil.which("vercel"):
            return ValidationResult(
                name="Vercel",
                success=False,
                message="Vercel CLI not installed",
                details="Install with: npm install -g vercel",
            )

        try:
            result = subprocess.run(
                ["vercel", "whoami"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                user = result.stdout.strip()
                return ValidationResult(
                    name="Vercel",
                    success=True,
                    message=f"Authenticated as {user}",
                )
            else:
                return ValidationResult(
                    name="Vercel",
                    success=False,
                    message="Not authenticated",
                    details="Run 'vercel login' to authenticate",
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                name="Vercel",
                success=False,
                message="Authentication check timed out",
            )
        except Exception as e:
            return ValidationResult(
                name="Vercel",
                success=False,
                message=f"Error: {e}",
            )

    def validate_fly(self) -> ValidationResult:
        """Validate Fly.io CLI authentication.

        Returns:
            ValidationResult with success status and details
        """
        fly_cmd = None
        for cmd in ["fly", "flyctl"]:
            if shutil.which(cmd):
                fly_cmd = cmd
                break

        if not fly_cmd:
            return ValidationResult(
                name="Fly.io",
                success=False,
                message="Fly CLI not installed",
                details="Install with: brew install flyctl",
            )

        try:
            result = subprocess.run(
                [fly_cmd, "auth", "whoami"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                user = result.stdout.strip()
                return ValidationResult(
                    name="Fly.io",
                    success=True,
                    message=f"Authenticated as {user}",
                )
            else:
                return ValidationResult(
                    name="Fly.io",
                    success=False,
                    message="Not authenticated",
                    details="Run 'fly auth login' to authenticate",
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                name="Fly.io",
                success=False,
                message="Authentication check timed out",
            )
        except Exception as e:
            return ValidationResult(
                name="Fly.io",
                success=False,
                message=f"Error: {e}",
            )

    def validate_neon(self) -> ValidationResult:
        """Validate Neon API key or database connection.

        Returns:
            ValidationResult with success status and details
        """
        api_key = os.environ.get("NEON_API_KEY")
        database_url = os.environ.get("DATABASE_URL", "")

        if api_key:
            # Validate API key
            try:
                import urllib.request

                req = urllib.request.Request(
                    "https://console.neon.tech/api/v2/projects",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Accept": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        return ValidationResult(
                            name="Neon",
                            success=True,
                            message="API key valid",
                        )
            except Exception as e:
                return ValidationResult(
                    name="Neon",
                    success=False,
                    message=f"API check failed: {e}",
                )

        if database_url.startswith("postgres") and "neon" in database_url:
            return ValidationResult(
                name="Neon",
                success=True,
                message="DATABASE_URL configured",
                details="Connection not tested (would require psycopg2)",
            )

        return ValidationResult(
            name="Neon",
            success=False,
            message="NEON_API_KEY or DATABASE_URL not set",
            details="Add to .env.local",
        )

    def validate_supabase(self) -> ValidationResult:
        """Validate Supabase configuration.

        Returns:
            ValidationResult with success status and details
        """
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

        if not url:
            return ValidationResult(
                name="Supabase",
                success=False,
                message="SUPABASE_URL not set",
                details="Add to .env.local",
            )

        if not key:
            return ValidationResult(
                name="Supabase",
                success=False,
                message="SUPABASE_KEY not set",
                details="Add SUPABASE_KEY or SUPABASE_ANON_KEY to .env.local",
            )

        # Try a health check
        try:
            import urllib.request

            req = urllib.request.Request(
                f"{url}/rest/v1/",
                headers={
                    "apikey": key,
                    "Authorization": f"Bearer {key}",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status in (200, 404):  # 404 is ok for empty schema
                    return ValidationResult(
                        name="Supabase",
                        success=True,
                        message="Connected successfully",
                    )
        except Exception as e:
            return ValidationResult(
                name="Supabase",
                success=False,
                message=f"Connection failed: {e}",
            )

        return ValidationResult(
            name="Supabase",
            success=True,
            message="Configured (connection not tested)",
        )

    def validate_sentry(self) -> ValidationResult:
        """Validate Sentry DSN configuration.

        Returns:
            ValidationResult with success status and details
        """
        dsn = os.environ.get("SENTRY_DSN")

        if not dsn:
            return ValidationResult(
                name="Sentry",
                success=False,
                message="SENTRY_DSN not set",
                details="Get DSN from sentry.io > Project > Settings > Client Keys",
            )

        # Validate DSN format
        if not dsn.startswith("https://") or ".ingest.sentry.io" not in dsn:
            return ValidationResult(
                name="Sentry",
                success=False,
                message="Invalid DSN format",
                details="DSN should be: https://xxx@xxx.ingest.sentry.io/xxx",
            )

        return ValidationResult(
            name="Sentry",
            success=True,
            message="DSN configured",
            details="Note: Actual error reporting not tested",
        )


def print_validation_results(results: list[ValidationResult]) -> None:
    """Print validation results in a formatted way.

    Args:
        results: List of ValidationResult objects
    """
    import click

    click.echo()
    click.echo("=" * 50)
    click.echo("  Live Integration Validation")
    click.echo("=" * 50)
    click.echo()

    passed = 0
    failed = 0

    for result in results:
        if result.success:
            status = click.style("PASS", fg="green")
            passed += 1
        else:
            status = click.style("FAIL", fg="red")
            failed += 1

        click.echo(f"  {status} {result.name}: {result.message}")
        if result.details and not result.success:
            click.echo(f"         {result.details}")

    click.echo()
    click.echo(f"  {passed} passed, {failed} failed")
    click.echo()
