"""Guided PR Autopilot setup preflight.

The canonical readiness check that runs *before* PR Autopilot is turned on for
live runs. It follows the operator experience the engine depends on:

* **infer first** — reuse :func:`configure_pr_autopilot` to write the declarative
  ``.vibe`` artifacts from the GitHub/Linear identity it can detect;
* **validate real prerequisites** — config, the runner's workflow assets, GitHub
  CLI auth, and the human-held Anthropic secret, plus soft observability checks
  (Linear logging, optional Axiom) that warn but never block;
* **gate enablement** — only leave the integration enabled when every *required*
  check passes; a failed preflight disables it again so a half-ready pilot never
  goes live;
* **show remediation** — each failure carries a concrete next step instead of a
  generic "read the docs".

The checklist lives here, in one place, so another agent can run or extend it
without rediscovering which prerequisites matter. Follow-on tickets deepen the
GitHub App, Linear-logging, and Axiom checks against real consumer projects.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from vibe.integrations.pr_autopilot.prototype import (
    ANTHROPIC_SECRET_NAME,
    CORE_CONFIG_PATH,
    DISABLED_CONFIG_PATH,
    INTEGRATION_CONFIG_PATH,
    ProviderRunner,
    ToolResult,
    _github_label,
    _probe_label,
    _read_toml,
    _run_provider_tool,
    _secret_present,
    configure_pr_autopilot,
    disable_pr_autopilot,
    enable_pr_autopilot,
)
from vibe.ui.validation import SetupValidator, ValidationResult

# The loop assets the cloud runner executes after opening a PR. Their presence is
# what makes a checkout able to *run* the autopilot, not just describe it.
WORKFLOW_ASSETS: tuple[Path, ...] = (
    Path(".claude/commands/pr-autopilot.md"),
    Path("recipes/workflows/pr-autopilot.md"),
)
AXIOM_TOKEN_ENV = "AXIOM_TOKEN"


@dataclass(frozen=True)
class PreflightCheck:
    """One readiness check plus whether it blocks enablement."""

    result: ValidationResult
    required: bool = True

    @property
    def label(self) -> str:
        if self.result.success:
            return "PASS"
        return "FAIL" if self.required else "WARN"

    @property
    def blocking(self) -> bool:
        return self.required and not self.result.success


@dataclass(frozen=True)
class PreflightReport:
    """The full preflight result: what was inferred and every check."""

    inferred_github: str
    inferred_linear_team: str
    checks: tuple[PreflightCheck, ...]

    @property
    def blocking_failures(self) -> tuple[PreflightCheck, ...]:
        return tuple(check for check in self.checks if check.blocking)

    @property
    def warnings(self) -> tuple[PreflightCheck, ...]:
        return tuple(
            check for check in self.checks if not check.required and not check.result.success
        )

    @property
    def ready(self) -> bool:
        return not self.blocking_failures


def setup_pr_autopilot(*, runner: ProviderRunner | None = None) -> str:
    """Infer, validate, and gate PR Autopilot enablement in one guided pass.

    Always (re)writes the inferred artifacts, then runs the preflight. When every
    required check passes the integration is enabled; otherwise it is disabled and
    the report lists exactly what to fix.
    """

    run_tool = runner or _run_provider_tool
    # Infer first: write/refresh the declarative artifacts the checks read.
    configure_pr_autopilot(runner=run_tool)
    report = run_preflight(runner=run_tool)
    if report.ready:
        enable_pr_autopilot(runner=run_tool)
        enabled = True
    else:
        disable_pr_autopilot()
        enabled = False
    return _format_setup_report(report, enabled=enabled)


def run_preflight(*, runner: ProviderRunner | None = None) -> PreflightReport:
    """Run every readiness check against the current ``.vibe`` artifacts + live state."""

    run_tool = runner or _run_provider_tool
    core = _read_toml(CORE_CONFIG_PATH)
    integration = _read_toml(INTEGRATION_CONFIG_PATH)
    if not integration and DISABLED_CONFIG_PATH.exists():
        integration = _read_toml(DISABLED_CONFIG_PATH)

    auth_probe = run_tool(("gh", "auth", "status"))
    secrets_probe = run_tool(("gh", "secret", "list", "--json", "name"))

    checks = (
        _check_core_config(core),
        _check_integration_config(integration),
        _check_workflow_assets(),
        _check_github_auth(auth_probe),
        _check_anthropic_secret(secrets_probe),
        _check_linear_logging(),
        _check_axiom_optional(),
    )
    linear = core.get("linear", {})
    return PreflightReport(
        inferred_github=_github_label(core),
        inferred_linear_team=str(linear.get("team") or "unset"),
        checks=checks,
    )


def _check_core_config(core: dict) -> PreflightCheck:
    github = core.get("github", {})
    owner = github.get("owner")
    repo = github.get("repo")
    if owner and repo:
        return PreflightCheck(
            ValidationResult("core config", True, f"{owner}/{repo} in {CORE_CONFIG_PATH}")
        )
    return PreflightCheck(
        ValidationResult(
            "core config",
            False,
            f"github owner/repo missing in {CORE_CONFIG_PATH}",
            "Could not infer from gh/git/legacy config; run: bin/vibe pr-autopilot configure",
        )
    )


def _check_integration_config(integration: dict) -> PreflightCheck:
    automation = integration.get("automation", {})
    secrets = integration.get("secrets", {})
    base_branch = automation.get("base_branch")
    secret_ref = secrets.get("anthropic_api_key")
    if base_branch and secret_ref:
        return PreflightCheck(
            ValidationResult(
                "integration config",
                True,
                f"base_branch={base_branch}, anthropic secret ref set",
            )
        )
    return PreflightCheck(
        ValidationResult(
            "integration config",
            False,
            f"{INTEGRATION_CONFIG_PATH} missing automation/secrets",
            "Run: bin/vibe pr-autopilot configure",
        )
    )


def _check_workflow_assets() -> PreflightCheck:
    missing = [str(path) for path in WORKFLOW_ASSETS if not path.exists()]
    if not missing:
        return PreflightCheck(
            ValidationResult("workflow assets", True, "PR-autopilot loop command + recipe present")
        )
    return PreflightCheck(
        ValidationResult(
            "workflow assets",
            False,
            f"missing: {', '.join(missing)}",
            "Restore the PR-autopilot loop assets from the vibe toolkit",
        )
    )


def _check_github_auth(auth_probe: ToolResult) -> PreflightCheck:
    if auth_probe.ok:
        return PreflightCheck(ValidationResult("github auth", True, "gh CLI authenticated"))
    return PreflightCheck(
        ValidationResult(
            "github auth",
            False,
            f"gh auth status -> {_probe_label(auth_probe)}",
            "Run: gh auth login",
        )
    )


def _check_anthropic_secret(secrets_probe: ToolResult) -> PreflightCheck:
    present = _secret_present(secrets_probe)
    if present is True:
        return PreflightCheck(
            ValidationResult(
                "anthropic secret", True, f"{ANTHROPIC_SECRET_NAME} present in GitHub Actions"
            )
        )
    if present is False:
        return PreflightCheck(
            ValidationResult(
                "anthropic secret",
                False,
                f"{ANTHROPIC_SECRET_NAME} missing from GitHub Actions secrets",
                "Ask the human for the Anthropic key, then run: "
                f"gh secret set {ANTHROPIC_SECRET_NAME}",
            )
        )
    return PreflightCheck(
        ValidationResult(
            "anthropic secret",
            False,
            f"could not read GitHub Actions secrets ({_probe_label(secrets_probe)})",
            f"Authenticate gh, then verify: gh secret list (expecting {ANTHROPIC_SECRET_NAME})",
        )
    )


def _check_linear_logging() -> PreflightCheck:
    # Compose the centralized validator (vibe.ui) so the Linear check stays in one
    # place. Soft: the engine degrades without it, so warn rather than block.
    base = SetupValidator({}).validate_linear()
    details = base.details
    if not base.success:
        details = "Set LINEAR_API_KEY for Linear-visible run telemetry (VIBE-146)"
    return PreflightCheck(
        ValidationResult("linear logging", base.success, base.message, details),
        required=False,
    )


def _check_axiom_optional() -> PreflightCheck:
    if os.environ.get(AXIOM_TOKEN_ENV):
        return PreflightCheck(
            ValidationResult("axiom (optional)", True, f"{AXIOM_TOKEN_ENV} set"),
            required=False,
        )
    return PreflightCheck(
        ValidationResult(
            "axiom (optional)",
            False,
            f"{AXIOM_TOKEN_ENV} not set",
            "Optional: set AXIOM_TOKEN to ship PR-autopilot run logs to Axiom",
        ),
        required=False,
    )


def _format_setup_report(report: PreflightReport, *, enabled: bool) -> str:
    lines = [
        "PR Autopilot setup",
        "Inferred:",
        f"  github: {report.inferred_github}",
        f"  linear team: {report.inferred_linear_team}",
        "Preflight checks:",
    ]
    for check in report.checks:
        result = check.result
        lines.append(f"  {check.label:<4} {result.name}: {result.message}")
        if result.details and not result.success:
            lines.append(f"       -> {result.details}")

    if report.ready:
        lines.append("Result: READY - all required checks passed; PR Autopilot enabled.")
        lines.append("Next: bin/vibe pr-autopilot status")
    else:
        count = len(report.blocking_failures)
        plural = "s" if count != 1 else ""
        lines.append(
            f"Result: NOT READY - {count} required check{plural} failed; "
            "PR Autopilot left disabled."
        )
        lines.append("Fix the FAIL items above, then re-run: bin/vibe pr-autopilot setup")
    return "\n".join(lines)
