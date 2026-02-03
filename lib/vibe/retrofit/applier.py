"""Apply retrofit actions to a project."""

import shutil
import subprocess
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import click

from lib.vibe.config import DEFAULT_CONFIG, save_config
from lib.vibe.retrofit.analyzer import ActionType, RetrofitAction, RetrofitPlan
from lib.vibe.state import DEFAULT_STATE, save_state


@dataclass
class ApplyResult:
    """Result of applying an action."""

    success: bool
    action_name: str
    message: str


class RetrofitApplier:
    """Applies retrofit actions to a project."""

    def __init__(
        self,
        project_path: Path | None = None,
        boilerplate_path: Path | None = None,
        dry_run: bool = False,
    ):
        """
        Initialize the applier.

        Args:
            project_path: Path to the project being retrofitted
            boilerplate_path: Path to the boilerplate source (for copying files)
            dry_run: If True, don't make changes, just report what would happen
        """
        self.project_path = project_path or Path.cwd()
        self.boilerplate_path = boilerplate_path
        self.dry_run = dry_run

        # Map action names to applier methods
        self._appliers: dict[str, Callable[[RetrofitAction], ApplyResult]] = {
            "vibe_config": self._apply_vibe_config,
            "main_branch": self._apply_main_branch,
            "branch_pattern": self._apply_branch_pattern,
            "worktrees": self._apply_worktrees,
            "github_actions": self._apply_github_actions,
            "pr_template": self._apply_pr_template,
            "github_labels": self._apply_github_labels,
        }

    def apply_plan(
        self,
        plan: RetrofitPlan,
        auto_only: bool = True,
        interactive: bool = True,
    ) -> list[ApplyResult]:
        """
        Apply actions from a retrofit plan.

        Args:
            plan: The retrofit plan to apply
            auto_only: Only apply auto-applicable actions
            interactive: Prompt for confirmation before each action

        Returns:
            List of apply results
        """
        results = []

        actions_to_apply = (
            plan.auto_applicable_actions if auto_only else [
                a for a in plan.actions
                if a.action_type in (ActionType.ADOPT, ActionType.CONFIGURE)
            ]
        )

        for action in actions_to_apply:
            if action.action_type == ActionType.SKIP:
                continue

            if interactive:
                if not click.confirm(f"Apply: {action.description}?", default=True):
                    results.append(
                        ApplyResult(False, action.name, "Skipped by user")
                    )
                    continue

            result = self.apply_action(action)
            results.append(result)

            if interactive:
                status = "✓" if result.success else "✗"
                click.echo(f"  {status} {result.message}")

        return results

    def apply_action(self, action: RetrofitAction) -> ApplyResult:
        """Apply a single action."""
        applier = self._appliers.get(action.name)
        if not applier:
            return ApplyResult(
                False,
                action.name,
                f"No applier found for action: {action.name}",
            )

        try:
            return applier(action)
        except Exception as e:
            return ApplyResult(False, action.name, f"Error: {e}")

    def _apply_vibe_config(self, action: RetrofitAction) -> ApplyResult:
        """Create .vibe/config.json with detected settings."""
        if self.dry_run:
            return ApplyResult(True, "vibe_config", "Would create .vibe/config.json")

        config = DEFAULT_CONFIG.copy()

        # Will be populated by other actions
        save_config(config, self.project_path)

        # Also create local state
        save_state(DEFAULT_STATE.copy(), self.project_path)

        return ApplyResult(True, "vibe_config", "Created .vibe/config.json and local_state.json")

    def _apply_main_branch(self, action: RetrofitAction) -> ApplyResult:
        """Configure main branch in vibe config."""
        if self.dry_run:
            branch = action.suggested_value or action.current_value or "main"
            return ApplyResult(True, "main_branch", f"Would set main branch to '{branch}'")

        from lib.vibe.config import load_config, save_config

        config = load_config(self.project_path)
        branch = action.suggested_value or action.current_value or "main"
        config.setdefault("branching", {})["main_branch"] = branch
        save_config(config, self.project_path)

        return ApplyResult(True, "main_branch", f"Set main branch to '{branch}'")

    def _apply_branch_pattern(self, action: RetrofitAction) -> ApplyResult:
        """Configure branch naming pattern."""
        if self.dry_run:
            pattern = action.suggested_value or "{PROJ}-{num}"
            return ApplyResult(True, "branch_pattern", f"Would set pattern to '{pattern}'")

        from lib.vibe.config import load_config, save_config

        config = load_config(self.project_path)
        pattern = action.suggested_value or "{PROJ}-{num}"
        config.setdefault("branching", {})["pattern"] = pattern
        save_config(config, self.project_path)

        return ApplyResult(True, "branch_pattern", f"Set branch pattern to '{pattern}'")

    def _apply_worktrees(self, action: RetrofitAction) -> ApplyResult:
        """Enable worktree configuration."""
        if self.dry_run:
            return ApplyResult(True, "worktrees", "Would configure worktree settings")

        from lib.vibe.config import load_config, save_config

        config = load_config(self.project_path)
        config["worktrees"] = {
            "location": "sibling",
            "base_path": "../{repo}-worktrees",
            "auto_cleanup": True,
        }
        save_config(config, self.project_path)

        return ApplyResult(True, "worktrees", "Configured worktree settings")

    def _apply_github_actions(self, action: RetrofitAction) -> ApplyResult:
        """Copy GitHub Actions workflows from boilerplate."""
        workflows_dir = self.project_path / ".github" / "workflows"

        if self.dry_run:
            return ApplyResult(
                True, "github_actions", f"Would create workflows in {workflows_dir}"
            )

        # Create directory if needed
        workflows_dir.mkdir(parents=True, exist_ok=True)

        # If we have a boilerplate path, copy from there
        if self.boilerplate_path:
            source_workflows = self.boilerplate_path / ".github" / "workflows"
            if source_workflows.is_dir():
                copied = []
                for workflow_file in source_workflows.glob("*.yml"):
                    dest = workflows_dir / workflow_file.name
                    if not dest.exists():
                        shutil.copy2(workflow_file, dest)
                        copied.append(workflow_file.name)

                if copied:
                    return ApplyResult(
                        True,
                        "github_actions",
                        f"Copied workflows: {', '.join(copied)}",
                    )
                else:
                    return ApplyResult(
                        True,
                        "github_actions",
                        "All workflows already exist",
                    )

        # If no boilerplate path, create minimal workflows
        created = []

        # PR policy workflow
        pr_policy = workflows_dir / "pr-policy.yml"
        if not pr_policy.exists():
            pr_policy.write_text(self._get_pr_policy_workflow())
            created.append("pr-policy.yml")

        # Security workflow
        security = workflows_dir / "security.yml"
        if not security.exists():
            security.write_text(self._get_security_workflow())
            created.append("security.yml")

        if created:
            return ApplyResult(
                True,
                "github_actions",
                f"Created workflows: {', '.join(created)}",
            )

        return ApplyResult(True, "github_actions", "Workflows already exist")

    def _apply_pr_template(self, action: RetrofitAction) -> ApplyResult:
        """Create PR template."""
        template_path = self.project_path / ".github" / "PULL_REQUEST_TEMPLATE.md"

        if self.dry_run:
            return ApplyResult(True, "pr_template", f"Would create {template_path}")

        if template_path.exists():
            return ApplyResult(True, "pr_template", "PR template already exists")

        template_path.parent.mkdir(parents=True, exist_ok=True)
        template_path.write_text(self._get_pr_template())

        return ApplyResult(True, "pr_template", "Created PR template")

    def _apply_github_labels(self, action: RetrofitAction) -> ApplyResult:
        """Create GitHub labels using gh CLI."""
        if self.dry_run:
            return ApplyResult(True, "github_labels", "Would create GitHub labels")

        # Check if gh CLI is available
        try:
            subprocess.run(
                ["gh", "--version"],
                capture_output=True,
                check=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError):
            return ApplyResult(
                False,
                "github_labels",
                "gh CLI not available. Install from https://cli.github.com/",
            )

        # Define labels to create
        labels = [
            # Type labels
            ("Bug", "d73a4a", "Something isn't working"),
            ("Feature", "a2eeef", "New feature or request"),
            ("Chore", "fef2c0", "Maintenance or cleanup"),
            ("Refactor", "c5def5", "Code improvement without behavior change"),
            # Risk labels
            ("Low Risk", "0e8a16", "Minimal scope, well-tested, low blast radius"),
            ("Medium Risk", "fbca04", "Moderate scope, may affect multiple components"),
            ("High Risk", "b60205", "Large scope, critical path, or infrastructure"),
            # Area labels
            ("Frontend", "1d76db", "UI and client-side code"),
            ("Backend", "5319e7", "Server, API, business logic"),
            ("Infra", "006b75", "DevOps, CI/CD, infrastructure"),
            ("Docs", "0075ca", "Documentation only"),
            # Special labels
            ("HUMAN", "d4c5f9", "Requires human decision or action"),
            ("Milestone", "bfdadc", "Part of a larger feature"),
            ("Blocked", "e99695", "Waiting on external dependency"),
        ]

        created = []
        already_exists = []
        failed = []

        for name, color, description in labels:
            result = subprocess.run(
                [
                    "gh", "label", "create", name,
                    "--color", color,
                    "--description", description,
                    "--force",  # Update if exists
                ],
                capture_output=True,
                text=True,
                cwd=str(self.project_path),
            )

            if result.returncode == 0:
                if "already exists" in result.stderr.lower():
                    already_exists.append(name)
                else:
                    created.append(name)
            else:
                failed.append(name)

        if failed:
            return ApplyResult(
                False,
                "github_labels",
                f"Created {len(created)}, failed {len(failed)}: {', '.join(failed)}",
            )

        return ApplyResult(
            True,
            "github_labels",
            f"Created {len(created)} labels, {len(already_exists)} already existed",
        )

    def _get_pr_template(self) -> str:
        """Get default PR template content."""
        return """## Summary

<!-- Brief description of the changes. Link to the ticket. -->

Closes #<!-- ticket number -->

## Changes

<!-- Bullet points of what changed -->

-

## Risk Assessment

<!-- Select one risk level and delete the others -->

- [ ] **Low Risk** - Minimal scope, well-tested, low blast radius
- [ ] **Medium Risk** - Moderate scope, may affect multiple components
- [ ] **High Risk** - Large scope, critical path, or infrastructure changes

## Testing

- [ ] Unit tests added/updated
- [ ] Manual testing instructions included (for non-trivial changes)

## Checklist

- [ ] Code follows project conventions
- [ ] No secrets or credentials committed
- [ ] PR title includes ticket reference
- [ ] Risk label added
"""

    def _get_pr_policy_workflow(self) -> str:
        """Get minimal PR policy workflow."""
        return """name: PR Policy

on:
  pull_request:
    types: [opened, edited, synchronize, labeled, unlabeled]

jobs:
  check-policy:
    runs-on: ubuntu-latest
    steps:
      - name: Check risk label
        uses: actions/github-script@v7
        with:
          script: |
            const labels = context.payload.pull_request.labels.map(l => l.name);
            const riskLabels = ['Low Risk', 'Medium Risk', 'High Risk'];
            const hasRiskLabel = labels.some(l => riskLabels.includes(l));

            if (!hasRiskLabel) {
              core.setFailed('PR must have a risk label (Low Risk, Medium Risk, or High Risk)');
            }
"""

    def _get_security_workflow(self) -> str:
        """Get minimal security workflow."""
        return """name: Security

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  gitleaks:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""
