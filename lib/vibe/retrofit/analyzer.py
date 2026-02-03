"""Analyze detected project profile and recommend retrofit actions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from lib.vibe.retrofit.detector import ProjectProfile


class ActionType(Enum):
    """Types of retrofit actions."""

    ADOPT = "adopt"  # New feature to adopt
    CONFIGURE = "configure"  # Existing feature needs configuration
    SKIP = "skip"  # Already configured or not applicable
    CONFLICT = "conflict"  # Existing config conflicts with boilerplate


class ActionPriority(Enum):
    """Priority levels for actions."""

    REQUIRED = "required"  # Must be done for basic functionality
    RECOMMENDED = "recommended"  # Strongly suggested
    OPTIONAL = "optional"  # Nice to have


@dataclass
class RetrofitAction:
    """A single retrofit action recommendation."""

    name: str
    action_type: ActionType
    priority: ActionPriority
    description: str
    current_value: Any = None
    suggested_value: Any = None
    auto_applicable: bool = True  # Can be auto-applied without user input
    details: str = ""


@dataclass
class RetrofitPlan:
    """Complete retrofit plan for a project."""

    actions: list[RetrofitAction] = field(default_factory=list)
    profile: ProjectProfile | None = None

    @property
    def required_actions(self) -> list[RetrofitAction]:
        """Get required actions."""
        return [a for a in self.actions if a.priority == ActionPriority.REQUIRED]

    @property
    def recommended_actions(self) -> list[RetrofitAction]:
        """Get recommended actions."""
        return [a for a in self.actions if a.priority == ActionPriority.RECOMMENDED]

    @property
    def optional_actions(self) -> list[RetrofitAction]:
        """Get optional actions."""
        return [a for a in self.actions if a.priority == ActionPriority.OPTIONAL]

    @property
    def conflicts(self) -> list[RetrofitAction]:
        """Get conflicting actions that need manual resolution."""
        return [a for a in self.actions if a.action_type == ActionType.CONFLICT]

    @property
    def auto_applicable_actions(self) -> list[RetrofitAction]:
        """Get actions that can be auto-applied."""
        return [
            a
            for a in self.actions
            if a.auto_applicable and a.action_type in (ActionType.ADOPT, ActionType.CONFIGURE)
        ]


class RetrofitAnalyzer:
    """Analyzes a project profile and generates a retrofit plan."""

    def __init__(self, profile: ProjectProfile):
        """Initialize analyzer with a project profile."""
        self.profile = profile

    def analyze(self) -> RetrofitPlan:
        """Generate a complete retrofit plan."""
        plan = RetrofitPlan(profile=self.profile)

        # Analyze each area and add actions
        self._analyze_vibe_config(plan)
        self._analyze_git_config(plan)
        self._analyze_github_config(plan)
        self._analyze_tracker_config(plan)
        self._analyze_deployment_config(plan)
        self._analyze_database_config(plan)
        self._analyze_labels(plan)

        return plan

    def _analyze_vibe_config(self, plan: RetrofitPlan) -> None:
        """Analyze existing vibe configuration."""
        if self.profile.has_vibe_config.detected:
            plan.actions.append(
                RetrofitAction(
                    name="vibe_config",
                    action_type=ActionType.SKIP,
                    priority=ActionPriority.REQUIRED,
                    description="Vibe configuration already exists",
                    current_value=self.profile.has_vibe_config.value,
                    details=self.profile.has_vibe_config.details,
                )
            )
        else:
            plan.actions.append(
                RetrofitAction(
                    name="vibe_config",
                    action_type=ActionType.ADOPT,
                    priority=ActionPriority.REQUIRED,
                    description="Create .vibe/config.json with project settings",
                    auto_applicable=True,
                )
            )

    def _analyze_git_config(self, plan: RetrofitPlan) -> None:
        """Analyze git configuration (main branch, branch pattern, worktrees)."""
        # Main branch detection
        if self.profile.main_branch.detected:
            main_branch = self.profile.main_branch.value
            if main_branch in ("main", "master"):
                plan.actions.append(
                    RetrofitAction(
                        name="main_branch",
                        action_type=ActionType.CONFIGURE,
                        priority=ActionPriority.REQUIRED,
                        description=f"Configure main branch as '{main_branch}'",
                        current_value=main_branch,
                        suggested_value=main_branch,
                        auto_applicable=True,
                        details=self.profile.main_branch.details,
                    )
                )
            else:
                plan.actions.append(
                    RetrofitAction(
                        name="main_branch",
                        action_type=ActionType.CONFLICT,
                        priority=ActionPriority.REQUIRED,
                        description=f"Unusual main branch detected: '{main_branch}'",
                        current_value=main_branch,
                        suggested_value="main",
                        auto_applicable=False,
                        details="Consider using 'main' or 'master' for compatibility",
                    )
                )
        else:
            plan.actions.append(
                RetrofitAction(
                    name="main_branch",
                    action_type=ActionType.CONFIGURE,
                    priority=ActionPriority.REQUIRED,
                    description="Configure main branch (defaulting to 'main')",
                    suggested_value="main",
                    auto_applicable=True,
                )
            )

        # Branch pattern
        if self.profile.branch_pattern.detected:
            pattern = self.profile.branch_pattern.value
            confidence = self.profile.branch_pattern.confidence
            if confidence >= 0.7:
                plan.actions.append(
                    RetrofitAction(
                        name="branch_pattern",
                        action_type=ActionType.CONFIGURE,
                        priority=ActionPriority.RECOMMENDED,
                        description=f"Use detected branch pattern: '{pattern}'",
                        current_value=pattern,
                        suggested_value=pattern,
                        auto_applicable=True,
                        details=self.profile.branch_pattern.details,
                    )
                )
            else:
                plan.actions.append(
                    RetrofitAction(
                        name="branch_pattern",
                        action_type=ActionType.CONFIGURE,
                        priority=ActionPriority.RECOMMENDED,
                        description="Configure branch naming pattern",
                        current_value=pattern,
                        suggested_value="{PROJ}-{num}",
                        auto_applicable=False,
                        details=f"Low confidence ({confidence:.0%}). Review before applying.",
                    )
                )
        else:
            plan.actions.append(
                RetrofitAction(
                    name="branch_pattern",
                    action_type=ActionType.ADOPT,
                    priority=ActionPriority.RECOMMENDED,
                    description="Add branch naming convention",
                    suggested_value="{PROJ}-{num}",
                    auto_applicable=True,
                    details="Using default pattern: {PROJ}-{num}",
                )
            )

        # Worktrees
        if self.profile.has_worktrees.detected:
            plan.actions.append(
                RetrofitAction(
                    name="worktrees",
                    action_type=ActionType.SKIP,
                    priority=ActionPriority.OPTIONAL,
                    description="Worktrees already in use",
                    current_value=self.profile.has_worktrees.value,
                    details=self.profile.has_worktrees.details,
                )
            )
        else:
            plan.actions.append(
                RetrofitAction(
                    name="worktrees",
                    action_type=ActionType.ADOPT,
                    priority=ActionPriority.RECOMMENDED,
                    description="Enable git worktrees for parallel development",
                    auto_applicable=True,
                    details="Worktrees isolate work per ticket, preventing conflicts",
                )
            )

    def _analyze_github_config(self, plan: RetrofitPlan) -> None:
        """Analyze GitHub configuration (actions, PR template)."""
        # GitHub Actions
        if self.profile.github_actions.detected:
            existing = self.profile.github_actions.value
            boilerplate_workflows = ["security", "pr-policy", "pr-opened", "pr-merged", "tests"]
            missing = [w for w in boilerplate_workflows if w not in existing]

            if missing:
                plan.actions.append(
                    RetrofitAction(
                        name="github_actions",
                        action_type=ActionType.ADOPT,
                        priority=ActionPriority.RECOMMENDED,
                        description=f"Add missing workflows: {', '.join(missing)}",
                        current_value=existing,
                        suggested_value=boilerplate_workflows,
                        auto_applicable=True,
                        details="Existing workflows will be preserved",
                    )
                )
            else:
                plan.actions.append(
                    RetrofitAction(
                        name="github_actions",
                        action_type=ActionType.SKIP,
                        priority=ActionPriority.RECOMMENDED,
                        description="All recommended workflows already exist",
                        current_value=existing,
                    )
                )
        else:
            plan.actions.append(
                RetrofitAction(
                    name="github_actions",
                    action_type=ActionType.ADOPT,
                    priority=ActionPriority.RECOMMENDED,
                    description="Add GitHub Actions workflows (CI, security, PR automation)",
                    auto_applicable=True,
                )
            )

        # PR Template
        if self.profile.has_pr_template.detected:
            plan.actions.append(
                RetrofitAction(
                    name="pr_template",
                    action_type=ActionType.SKIP,
                    priority=ActionPriority.OPTIONAL,
                    description="PR template already exists",
                    current_value=self.profile.has_pr_template.value,
                )
            )
        else:
            plan.actions.append(
                RetrofitAction(
                    name="pr_template",
                    action_type=ActionType.ADOPT,
                    priority=ActionPriority.RECOMMENDED,
                    description="Add PR template with risk assessment checklist",
                    auto_applicable=True,
                )
            )

    def _analyze_tracker_config(self, plan: RetrofitPlan) -> None:
        """Analyze ticket tracker configuration."""
        if self.profile.linear_integration.detected:
            plan.actions.append(
                RetrofitAction(
                    name="tracker",
                    action_type=ActionType.CONFIGURE,
                    priority=ActionPriority.RECOMMENDED,
                    description="Configure Linear integration",
                    current_value="linear",
                    suggested_value="linear",
                    auto_applicable=False,
                    details="Linear detected. Run 'bin/vibe setup -w tracker' to configure.",
                )
            )
        elif self.profile.shortcut_integration.detected:
            plan.actions.append(
                RetrofitAction(
                    name="tracker",
                    action_type=ActionType.CONFIGURE,
                    priority=ActionPriority.RECOMMENDED,
                    description="Configure Shortcut integration",
                    current_value="shortcut",
                    suggested_value="shortcut",
                    auto_applicable=False,
                    details="Shortcut detected. Run 'bin/vibe setup -w tracker' to configure.",
                )
            )
        else:
            plan.actions.append(
                RetrofitAction(
                    name="tracker",
                    action_type=ActionType.ADOPT,
                    priority=ActionPriority.OPTIONAL,
                    description="Add ticket tracker integration (Linear/Shortcut)",
                    auto_applicable=False,
                    details="Run 'bin/vibe setup -w tracker' when ready",
                )
            )

    def _analyze_deployment_config(self, plan: RetrofitPlan) -> None:
        """Analyze deployment configuration."""
        # Vercel
        if self.profile.vercel_config.detected:
            plan.actions.append(
                RetrofitAction(
                    name="vercel",
                    action_type=ActionType.SKIP,
                    priority=ActionPriority.OPTIONAL,
                    description="Vercel already configured",
                    current_value=self.profile.vercel_config.value,
                    details=self.profile.vercel_config.details,
                )
            )

        # Fly.io
        if self.profile.fly_config.detected:
            plan.actions.append(
                RetrofitAction(
                    name="fly",
                    action_type=ActionType.SKIP,
                    priority=ActionPriority.OPTIONAL,
                    description="Fly.io already configured",
                    current_value=self.profile.fly_config.value,
                    details=self.profile.fly_config.details,
                )
            )

        # If no deployment configured, suggest options
        if not self.profile.vercel_config.detected and not self.profile.fly_config.detected:
            plan.actions.append(
                RetrofitAction(
                    name="deployment",
                    action_type=ActionType.ADOPT,
                    priority=ActionPriority.OPTIONAL,
                    description="Configure deployment (Vercel or Fly.io)",
                    auto_applicable=False,
                    details="Run 'bin/vibe setup -w vercel' or 'bin/vibe setup -w fly'",
                )
            )

    def _analyze_database_config(self, plan: RetrofitPlan) -> None:
        """Analyze database configuration."""
        if self.profile.supabase_config.detected:
            plan.actions.append(
                RetrofitAction(
                    name="database",
                    action_type=ActionType.SKIP,
                    priority=ActionPriority.OPTIONAL,
                    description="Supabase already configured",
                    current_value="supabase",
                    details=self.profile.supabase_config.details,
                )
            )
        elif self.profile.neon_config.detected:
            plan.actions.append(
                RetrofitAction(
                    name="database",
                    action_type=ActionType.SKIP,
                    priority=ActionPriority.OPTIONAL,
                    description="Neon already configured",
                    current_value="neon",
                    details=self.profile.neon_config.details,
                )
            )
        elif self.profile.database_type.detected:
            plan.actions.append(
                RetrofitAction(
                    name="database",
                    action_type=ActionType.SKIP,
                    priority=ActionPriority.OPTIONAL,
                    description=f"{self.profile.database_type.value} database detected",
                    current_value=self.profile.database_type.value,
                    details=self.profile.database_type.details,
                )
            )

    def _analyze_labels(self, plan: RetrofitPlan) -> None:
        """Analyze GitHub labels."""
        plan.actions.append(
            RetrofitAction(
                name="github_labels",
                action_type=ActionType.ADOPT,
                priority=ActionPriority.RECOMMENDED,
                description="Create standard GitHub labels (type, risk, area)",
                auto_applicable=True,
                details="Creates labels: Bug, Feature, Chore, Low/Medium/High Risk, etc.",
            )
        )

    def generate_summary(self, plan: RetrofitPlan) -> str:
        """Generate a human-readable summary of the retrofit plan."""
        lines = []
        lines.append("=" * 60)
        lines.append("  Retrofit Analysis Summary")
        lines.append("=" * 60)
        lines.append("")

        # Detected configuration
        lines.append("Detected Configuration:")
        lines.append("-" * 30)

        if self.profile.main_branch.detected:
            lines.append(f"  Main branch: {self.profile.main_branch.value}")
        if self.profile.branch_pattern.detected:
            conf = self.profile.branch_pattern.confidence
            lines.append(
                f"  Branch pattern: {self.profile.branch_pattern.value} ({conf:.0%} conf.)"
            )
        if self.profile.frontend_framework.detected:
            lines.append(f"  Frontend: {self.profile.frontend_framework.value}")
        if self.profile.backend_framework.detected:
            lines.append(f"  Backend: {self.profile.backend_framework.value}")
        if self.profile.package_manager.detected:
            lines.append(f"  Package manager: {self.profile.package_manager.value}")
        if self.profile.vercel_config.detected:
            lines.append("  Deployment: Vercel")
        if self.profile.fly_config.detected:
            lines.append("  Deployment: Fly.io")
        if self.profile.supabase_config.detected:
            lines.append("  Database: Supabase")
        if self.profile.test_framework.detected:
            lines.append(f"  Testing: {self.profile.test_framework.value}")

        lines.append("")

        # Required actions
        if plan.required_actions:
            lines.append("Required Actions:")
            lines.append("-" * 30)
            for action in plan.required_actions:
                status = "[AUTO]" if action.auto_applicable else "[MANUAL]"
                lines.append(f"  {status} {action.description}")
            lines.append("")

        # Recommended actions
        recommended = [
            a
            for a in plan.recommended_actions
            if a.action_type in (ActionType.ADOPT, ActionType.CONFIGURE)
        ]
        if recommended:
            lines.append("Recommended Actions:")
            lines.append("-" * 30)
            for action in recommended:
                status = "[AUTO]" if action.auto_applicable else "[MANUAL]"
                lines.append(f"  {status} {action.description}")
            lines.append("")

        # Conflicts
        if plan.conflicts:
            lines.append("Conflicts (manual resolution needed):")
            lines.append("-" * 30)
            for action in plan.conflicts:
                lines.append(f"  ! {action.description}")
                lines.append(f"    Current: {action.current_value}")
                lines.append(f"    Suggested: {action.suggested_value}")
            lines.append("")

        # Skipped (already configured)
        skipped = [a for a in plan.actions if a.action_type == ActionType.SKIP]
        if skipped:
            lines.append("Already Configured (skipped):")
            lines.append("-" * 30)
            for action in skipped:
                lines.append(f"  ✓ {action.description}")
            lines.append("")

        return "\n".join(lines)
