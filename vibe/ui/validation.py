"""Live integration validation for setup wizard.

Required vs optional integrations (VIBE-144)
--------------------------------------------
A packaged pilot must prove its *critical* external integrations are usable
before the first live run, and stay valid when *optional* ones are absent:

* **GitHub (required)** — the pilot opens PRs and sets labels, so the token
  must carry write access to the configured repo. :meth:`validate_github`
  proves that, not just that authentication succeeded.
* **Linear (required)** — failure visibility (the ``LinearTelemetrySink`` that
  comments terminal failures back onto the run's issue) and post-run reporting
  depend on a valid key and a reachable team. :meth:`validate_linear` proves
  those prerequisites.
* **Axiom (optional)** — extra telemetry. :meth:`validate_axiom` runs only when
  ``observability.axiom.enabled``; when Axiom is absent the flow stays valid as
  long as the required Linear-visible telemetry works. Its result is flagged
  ``optional`` so consumers (e.g. ``doctor``) can degrade a failure to a warning
  rather than a hard failure.

Results carry an ``optional`` flag so the required/optional distinction is
unambiguous at the point of consumption.
"""

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

# GitHub repo permission levels that let the pilot push branches, open PRs, and
# set labels. Below WRITE (READ/TRIAGE/NONE) the pilot cannot do its required
# actions.
_GITHUB_WRITE_LEVELS = frozenset({"WRITE", "MAINTAIN", "ADMIN"})

_LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"
_AXIOM_APL_URL = "https://api.axiom.co/v1/datasets/_apl?format=tabular"
_AXIOM_DEFAULT_DATASET = "app-logs"


@dataclass
class ValidationResult:
    """Result of a validation check.

    ``optional`` marks an integration the pilot can run without (e.g. Axiom).
    Consumers may render an optional failure as a warning rather than a hard
    failure; required-integration results leave it ``False``.
    """

    name: str
    success: bool
    message: str
    details: str | None = None
    optional: bool = False


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

        # Optional telemetry: Axiom only validates when explicitly enabled.
        # When absent the pilot stays valid (Linear telemetry is the required
        # failure-visibility path).
        if self.config.get("observability", {}).get("axiom", {}).get("enabled"):
            results.append(self.validate_axiom())

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
        except (subprocess.CalledProcessError, OSError) as e:
            return ValidationResult(
                name="GitHub",
                success=False,
                message=f"Error checking auth: {e}",
            )

        # Check repo access AND that the token carries the write access the
        # pilot needs to push branches, open PRs, and set labels. Authentication
        # alone is not enough — a read-only token authenticates fine but cannot
        # do the pilot's required actions, which is exactly the late failure
        # this check exists to prevent.
        owner = self.config.get("github", {}).get("owner")
        repo = self.config.get("github", {}).get("repo")

        if owner and repo:
            try:
                result = subprocess.run(
                    [
                        "gh",
                        "repo",
                        "view",
                        f"{owner}/{repo}",
                        "--json",
                        "name,viewerPermission",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
            except subprocess.TimeoutExpired:
                return ValidationResult(
                    name="GitHub",
                    success=False,
                    message="Repo check timed out",
                )

            if result.returncode != 0:
                return ValidationResult(
                    name="GitHub",
                    success=False,
                    message=f"Cannot access {owner}/{repo}",
                    details=result.stderr.strip() if result.stderr else None,
                )

            try:
                permission = (
                    json.loads(result.stdout or "{}").get("viewerPermission") or ""
                ).upper()
            except json.JSONDecodeError:
                permission = ""

            if permission in _GITHUB_WRITE_LEVELS:
                return ValidationResult(
                    name="GitHub",
                    success=True,
                    message=(
                        f"Connected to {owner}/{repo} "
                        f"({permission.title()}); can open PRs, set labels, read checks"
                    ),
                )

            current = permission.title() if permission else "unknown"
            return ValidationResult(
                name="GitHub",
                success=False,
                message=f"Insufficient permission on {owner}/{repo} for the pilot",
                details=(
                    f"The pilot needs Write access to push branches, open PRs, and "
                    f"set labels; current access is {current}. Ask a repo admin to "
                    f"grant Write, or re-authenticate with a token that has the "
                    f"'repo' scope (gh auth login --scopes repo)."
                ),
            )

        return ValidationResult(
            name="GitHub",
            success=True,
            message="Authenticated (no repo configured)",
            details=(
                "Set github.owner/github.repo so setup can verify the pilot has "
                "write access before the first run."
            ),
        )

    def _linear_graphql(
        self, api_key: str, query: str, variables: dict[str, Any] | None = None
    ) -> tuple[int, dict[str, Any]]:
        """POST a GraphQL query to Linear; return (status, parsed body).

        Body parsing is best-effort: a non-JSON / unreadable body yields ``{}``
        so callers can branch on ``status`` alone when they only need liveness.
        """
        payload: dict[str, Any] = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        req = urllib.request.Request(
            _LINEAR_GRAPHQL_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": api_key,
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                raw = response.read()
        except urllib.error.HTTPError as e:
            # A revoked/invalid key (or an unreachable team) surfaces as an HTTP
            # 4xx. Return the code instead of letting it propagate so callers can
            # branch on ``status`` and give an actionable message rather than a
            # raw "HTTP Error 401" string.
            status = e.code
            raw = e.read() or b""
        try:
            body = json.loads(raw)
        except (TypeError, ValueError):
            body = {}
        return status, (body if isinstance(body, dict) else {})

    def validate_linear(self) -> ValidationResult:
        """Validate the Linear prerequisites for human-visible failure logging.

        Proves more than "the key works": the pilot's ``LinearTelemetrySink``
        comments terminal failures back onto the run's issue and post-run
        reporting files into a team, so this checks the key is valid *and*, when
        a team is configured, that the team is reachable with that key.

        Returns:
            ValidationResult with success status and details
        """
        api_key = os.environ.get("LINEAR_API_KEY")

        if not api_key:
            return ValidationResult(
                name="Linear",
                success=False,
                message="LINEAR_API_KEY not set",
                details="Add to .env.local — failure logging and reporting need it",
            )

        # 1. Is the key valid at all?
        try:
            status, _ = self._linear_graphql(api_key, "{ viewer { id name } }")
        except (urllib.error.URLError, OSError, ValueError) as e:
            return ValidationResult(
                name="Linear",
                success=False,
                message=f"API check failed: {e}",
            )

        if status != 200:
            return ValidationResult(
                name="Linear",
                success=False,
                message=f"API returned {status}",
                details="Check the LINEAR_API_KEY value (it may be revoked)",
            )

        # 2. Failure-visibility/reporting prerequisite: a reachable team. Without
        #    a configured team the key is valid but post-run reporting has
        #    nowhere to file — surface that as actionable guidance, not a hard
        #    failure (the failure-comment path keys off the run's issue id).
        team_id = self.config.get("tracker", {}).get("config", {}).get("team_id")
        if not team_id:
            return ValidationResult(
                name="Linear",
                success=True,
                message="API key valid",
                details=(
                    "No tracker.config.team_id set — post-run Linear reporting "
                    "needs a team. Run 'bin/vibe setup -w tracker' to select one."
                ),
            )

        try:
            team_status, body = self._linear_graphql(
                api_key,
                "query Team($id: String!) { team(id: $id) { id name } }",
                {"id": team_id},
            )
        except (urllib.error.URLError, OSError, ValueError) as e:
            return ValidationResult(
                name="Linear",
                success=False,
                message=f"Team check failed: {e}",
            )

        team = (body.get("data") or {}).get("team") if team_status == 200 else None
        if team and team.get("id"):
            return ValidationResult(
                name="Linear",
                success=True,
                message=(
                    f"API key valid; team '{team.get('name') or team_id}' "
                    f"reachable (failure logging ready)"
                ),
            )

        return ValidationResult(
            name="Linear",
            success=False,
            message="Configured Linear team not accessible",
            details=(
                f"team_id '{team_id}' did not resolve with this API key. Failure "
                f"logging and post-run reporting file here — fix "
                f"tracker.config.team_id or use a key with access "
                f"(bin/vibe setup -w tracker)."
            ),
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
        except (urllib.error.URLError, OSError, ValueError) as e:
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
        except (subprocess.CalledProcessError, OSError) as e:
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
        except (subprocess.CalledProcessError, OSError) as e:
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
            except (urllib.error.URLError, OSError, ValueError) as e:
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
        except (urllib.error.URLError, OSError, ValueError) as e:
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

    def validate_axiom(self) -> ValidationResult:
        """Validate optional Axiom log wiring when configured.

        Axiom is optional telemetry: this only runs when
        ``observability.axiom.enabled``. It mirrors ``bin/logs health`` — a
        trivial APL query against the configured dataset using the same
        token/org headers — so a green check here means the pilot can actually
        ship and query logs. Every result is flagged ``optional`` so a failure
        degrades to a warning rather than blocking the pilot.

        Returns:
            ValidationResult with success status and details (always optional)
        """
        token = os.environ.get("AXIOM_API_TOKEN")
        org = os.environ.get("AXIOM_ORG_ID")
        dataset = (
            os.environ.get("AXIOM_DATASET")
            or self.config.get("observability", {}).get("axiom", {}).get("dataset")
            or _AXIOM_DEFAULT_DATASET
        )

        missing = [
            name for name, value in (("AXIOM_API_TOKEN", token), ("AXIOM_ORG_ID", org)) if not value
        ]
        if missing:
            return ValidationResult(
                name="Axiom",
                success=False,
                message=f"{', '.join(missing)} not set",
                details=(
                    "Add to .env.local (see recipes/observability/axiom.md). Axiom "
                    "is optional — Linear telemetry remains the required "
                    "failure-visibility path."
                ),
                optional=True,
            )

        # token and org are guaranteed set here (missing list was empty)
        assert token is not None and org is not None
        try:
            req = urllib.request.Request(
                _AXIOM_APL_URL,
                data=json.dumps({"apl": f"['{dataset}'] | take 1"}).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Axiom-Org-Id": org,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return ValidationResult(
                        name="Axiom",
                        success=True,
                        message=f"Connected to dataset '{dataset}'",
                        optional=True,
                    )
                return ValidationResult(
                    name="Axiom",
                    success=False,
                    message=f"API returned {response.status}",
                    optional=True,
                )
        except urllib.error.HTTPError as e:
            if e.code == 401:
                detail = "Token rejected — check AXIOM_API_TOKEN (needs Query scope)."
            elif e.code == 404:
                detail = (
                    f"Dataset '{dataset}' not found — check AXIOM_DATASET / create "
                    f"the dataset in the Axiom UI."
                )
            else:
                detail = "Verify AXIOM_API_TOKEN, AXIOM_ORG_ID, and AXIOM_DATASET."
            return ValidationResult(
                name="Axiom",
                success=False,
                message=f"API returned {e.code}",
                details=detail,
                optional=True,
            )
        except (urllib.error.URLError, OSError, ValueError) as e:
            return ValidationResult(
                name="Axiom",
                success=False,
                message=f"Connection failed: {e}",
                optional=True,
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
    optional_failed = 0

    for result in results:
        if result.success:
            status = click.style("PASS", fg="green")
            passed += 1
        elif result.optional:
            # An optional integration (e.g. Axiom) the pilot can run without —
            # surface it as a warning, not a hard failure.
            status = click.style("WARN", fg="yellow")
            optional_failed += 1
        else:
            status = click.style("FAIL", fg="red")
            failed += 1

        tag = " (optional)" if result.optional else ""
        click.echo(f"  {status} {result.name}{tag}: {result.message}")
        if result.details and not result.success:
            click.echo(f"         {result.details}")

    click.echo()
    summary = f"  {passed} passed, {failed} failed"
    if optional_failed:
        summary += f", {optional_failed} optional warning(s)"
    click.echo(summary)
    click.echo()
