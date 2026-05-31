"""Turn detected config/workflow drift into a reviewable remediation PR.

The setup preflight (:mod:`vibe.integrations.pr_autopilot.setup`) *detects* when
the assets PR Autopilot depends on are missing — but it can only print a "restore
these by hand" hint. This module closes that loop: it scans the same expected
assets, and when any are missing it can write them from the bundled toolkit
templates and open a **minimal, opt-in remediation PR** against the repo's base
branch, so setup is guided all the way to a reviewable repo change.

Design choices that keep the remediation *safe* (per VIBE-145 acceptance
criteria):

* **Missing assets only.** A file that already exists is never touched, even if
  its contents have drifted — the diff is therefore always pure additions, never
  an overwrite of an operator's edits. (Content-drift reconciliation is a
  deliberate follow-up.)
* **Opt-in.** Nothing is committed or pushed until the operator confirms. The
  default flow shows exactly what would be added and asks; a ``dry_run`` returns
  the plan without creating a branch.
* **Policy-compatible.** The opened PR targets the base branch with a body that
  follows ``.github/PULL_REQUEST_TEMPLATE.md`` and is reviewed by CodeRabbit on
  the normal path — the remediation never bypasses review.

The asset list is a superset of the preflight's :data:`WORKFLOW_ASSETS` (the
PR-autopilot loop command + recipe) plus the governance assets a consumer repo
needs to satisfy DEAL's PR policy/review flow.
"""

from __future__ import annotations

import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from vibe.integrations.pr_autopilot.prototype import (
    INTEGRATION_CONFIG_PATH,
    ProviderRunner,
    ToolResult,
    _run_provider_tool,
)
from vibe.integrations.pr_autopilot.setup import WORKFLOW_ASSETS

# Where remediation PRs are staged. Deterministic so a re-run is obvious (and a
# stale branch surfaces as a clear git error rather than silent divergence).
REMEDIATION_BRANCH = "pr-autopilot-config-remediation"
PR_TITLE = "chore: install PR Autopilot config assets"
COMMIT_MESSAGE = "chore: install PR Autopilot config assets"
_ASSET_PACKAGE = "vibe.integrations.pr_autopilot"
_ASSET_DIR = "remediation_assets"


@dataclass(frozen=True)
class RemediableAsset:
    """An expected config/workflow asset and the bundled template that fills it."""

    path: Path
    template: str
    description: str

    def render(self) -> str:
        """Read the bundled template content for this asset."""
        resource = files(_ASSET_PACKAGE).joinpath(_ASSET_DIR, self.template)
        return resource.read_text(encoding="utf-8")


# The assets a consumer repo needs for PR Autopilot. The loop subset
# (.claude command + recipe) mirrors the preflight's WORKFLOW_ASSETS; the
# governance subset is what makes an opened PR satisfy DEAL's policy + review.
REMEDIABLE_ASSETS: tuple[RemediableAsset, ...] = (
    RemediableAsset(
        Path(".claude/commands/pr-autopilot.md"),
        "pr-autopilot.command.md",
        "PR-autopilot loop command (the runner executes this after opening a PR)",
    ),
    RemediableAsset(
        Path("recipes/workflows/pr-autopilot.md"),
        "pr-autopilot.recipe.md",
        "PR-autopilot loop recipe",
    ),
    RemediableAsset(
        Path(".github/workflows/pr-policy.yml"),
        "pr-policy.yml",
        "PR policy gate (ticket reference + risk label checks)",
    ),
    RemediableAsset(
        Path(".github/PULL_REQUEST_TEMPLATE.md"),
        "PULL_REQUEST_TEMPLATE.md",
        "PR description template",
    ),
    RemediableAsset(
        Path(".coderabbit.yaml"),
        "coderabbit.yaml",
        "CodeRabbit review firewall config",
    ),
)


@dataclass(frozen=True)
class RemediationItem:
    """One missing asset plus the template content that will be written for it."""

    asset: RemediableAsset
    content: str


@dataclass(frozen=True)
class RemediationPlan:
    """The set of missing assets a remediation PR would add."""

    items: tuple[RemediationItem, ...]

    @property
    def empty(self) -> bool:
        return not self.items

    @property
    def paths(self) -> tuple[str, ...]:
        return tuple(str(item.asset.path) for item in self.items)


def detect_remediation_plan(*, root: Path | None = None) -> RemediationPlan:
    """Scan the expected assets and plan to create only the ones that are missing."""
    base = root or Path(".")
    items = tuple(
        RemediationItem(asset, asset.render())
        for asset in REMEDIABLE_ASSETS
        if not (base / asset.path).exists()
    )
    return RemediationPlan(items)


def remediate_pr_autopilot(
    *,
    runner: ProviderRunner | None = None,
    confirm: Callable[[str], bool] | None = None,
    root: Path | None = None,
    dry_run: bool = False,
) -> str:
    """Detect missing config assets and, with consent, open a remediation PR.

    The default (CLI) flow is interactive and opt-in: it shows the plan and asks
    before creating a branch. Pass ``dry_run=True`` to get the plan without
    touching git, or a ``confirm`` callable (``preview -> bool``) to drive the
    decision programmatically.
    """
    base = root or Path(".")
    plan = detect_remediation_plan(root=base)
    if plan.empty:
        return "All PR Autopilot config assets are present; nothing to remediate."

    preview = _render_preview(plan)
    if dry_run:
        return f"{preview}\n\nDry run: no branch created and no PR opened."

    decide = confirm if callable(confirm) else _confirm_via_input
    if not decide(preview):
        return f"{preview}\n\nDeclined: no remediation PR opened."

    return _open_remediation_pr(plan, runner=runner, root=base)


def _render_preview(plan: RemediationPlan) -> str:
    lines = [
        "PR Autopilot config remediation",
        f"Missing assets to add ({len(plan.items)}):",
    ]
    for item in plan.items:
        line_count = item.content.count("\n") + 1
        lines.append(f"  + {item.asset.path} ({line_count} lines) — {item.asset.description}")
    lines.append(
        "Each asset is created only because it is missing; nothing existing is overwritten."
    )
    return "\n".join(lines)


def _confirm_via_input(preview: str) -> bool:
    print(preview)
    answer = input("Open a remediation PR with these assets? [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def _open_remediation_pr(
    plan: RemediationPlan,
    *,
    runner: ProviderRunner | None,
    root: Path,
) -> str:
    run = runner or _run_provider_tool
    base_branch = _base_branch()

    # Branch first, so a failed checkout (e.g. the branch already exists) leaves
    # the working tree untouched rather than stranding written files on main.
    checkout = run(("git", "checkout", "-b", REMEDIATION_BRANCH))
    if not checkout.ok:
        return _step_failure("create branch", checkout)

    for item in plan.items:
        target = root / item.asset.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item.content, encoding="utf-8")

    steps: tuple[tuple[str, ...], ...] = (
        ("git", "add", *plan.paths),
        ("git", "commit", "-m", COMMIT_MESSAGE),
        ("git", "push", "-u", "origin", REMEDIATION_BRANCH),
        (
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            REMEDIATION_BRANCH,
            "--title",
            PR_TITLE,
            "--body",
            _pr_body(plan),
        ),
    )
    last = checkout
    for step in steps:
        last = run(step)
        if not last.ok:
            return _step_failure(step[0] + " " + step[1] if len(step) > 1 else step[0], last)

    pr_ref = last.stdout.strip() or "(see GitHub)"
    return (
        f"Opened remediation PR against '{base_branch}' from '{REMEDIATION_BRANCH}'.\n"
        f"  added: {', '.join(plan.paths)}\n"
        f"  pr: {pr_ref}\n"
        "CodeRabbit will review it on the normal path; merge once it is green."
    )


def _step_failure(step_label: str, result: ToolResult) -> str:
    detail = (result.stderr or result.stdout).strip() or f"exit {result.returncode}"
    return (
        f"Remediation stopped: could not {step_label}.\n"
        f"  {result.display} -> {detail}\n"
        "Resolve the issue (e.g. delete a stale branch or authenticate gh), then re-run."
    )


def _base_branch() -> str:
    """Resolve the PR base branch from the integration config, defaulting to main."""
    if INTEGRATION_CONFIG_PATH.exists():
        try:
            config = tomllib.loads(INTEGRATION_CONFIG_PATH.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, OSError):
            config = {}
        base = config.get("automation", {}).get("base_branch")
        if base:
            return str(base)
    return "main"


def _pr_body(plan: RemediationPlan) -> str:
    bullets = "\n".join(
        f"- Add `{item.asset.path}` — {item.asset.description}" for item in plan.items
    )
    return (
        "## Summary\n\n"
        "Installs the PR Autopilot config/workflow assets that `vibe pr-autopilot "
        "setup` detected were missing, so the repo has the loop assets and the "
        "policy/review baseline PR Autopilot depends on.\n\n"
        "## Changes\n\n"
        f"{bullets}\n\n"
        "## Risk Assessment\n\n"
        "- [x] **Low Risk** - additive only; no existing file is modified.\n\n"
        "## Testing\n\n"
        "- [x] Assets are bundled, validated templates; this PR only adds files.\n\n"
        "## Checklist\n\n"
        "- [x] Code follows project conventions\n"
        "- [x] No secrets or credentials committed\n"
        "- [x] Additive remediation; safe to review and merge\n"
    )


# Consistency guard: the loop subset of REMEDIABLE_ASSETS must stay in lockstep
# with the preflight's WORKFLOW_ASSETS so detection and remediation agree on
# exactly which loop assets matter.
_LOOP_PATHS = {asset.path for asset in REMEDIABLE_ASSETS}
assert set(WORKFLOW_ASSETS).issubset(_LOOP_PATHS), (
    "WORKFLOW_ASSETS drifted from REMEDIABLE_ASSETS; keep the loop asset paths in sync"
)
