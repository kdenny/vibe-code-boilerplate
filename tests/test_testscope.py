"""Unit tests for module-scoped test selection (vibe/testscope.py)."""

from __future__ import annotations

import pytest

from vibe.testscope import (
    INTEGRATION_SEAMS,
    RUN_ALL,
    SOURCE_TEST_MAP,
    discover_test_stems,
    select_test_targets,
)
from vibe.testscope import (
    main as testscope_main,
)

# A representative slice of the real suite's stems. Kept explicit so the tests
# don't depend on the live tests/ directory contents.
KNOWN = {
    "config",
    "errors",
    "tools",
    "version",
    "update_check",
    "doctor",
    "label_sync",
    "cli_main_pr",
    "cli_registry",
    "cli_ticket",
    "duplicate_pr_prevention",
    "trackers_linear",
    "trackers_shortcut",
    "trackers_github_issues",
    "views",
    "costs_alerts",
    "costs_base",
    "costs_cli",
    "costs_providers",
    "costs_provider_vercel",
    "costs_registry",
    "costs_wizard",
    "wizards_github",
    "setup",
    "secrets_providers",
    "git_worktrees",
    "frontend",
    "agents",
    "import_surface",
    "integrations",
    "integrations_guardrails",
    "retrofit",
}


def select(*changed: str) -> list[str] | str:
    return select_test_targets(changed, KNOWN)


class TestSharedPathsRunEverything:
    @pytest.mark.parametrize(
        "path",
        [
            "pyproject.toml",
            "tests/conftest.py",
            "vibe/__init__.py",
            "vibe/config.py",
            "vibe/config_schema.py",
            "vibe/env.py",
            "vibe/utils/cache.py",
            "vibe/testscope.py",
            ".github/workflows/tests.yml",
        ],
    )
    def test_shared_path_forces_full_suite(self, path: str) -> None:
        assert select(path) == RUN_ALL

    def test_shared_path_wins_even_alongside_scoped_change(self) -> None:
        # If anything shared changed, the whole suite runs regardless of what
        # else is in the diff.
        assert select("vibe/costs/providers/vercel.py", "pyproject.toml") == RUN_ALL


class TestPackageScoping:
    def test_costs_package_selects_all_costs_suites(self) -> None:
        targets = select("vibe/costs/providers/vercel.py")
        # The convention prefix "costs_" also matches test_costs_wizard.py.
        # That suite actually covers wizards/costs.py, so it's a slight
        # over-selection — but over-selection is the safe direction (extra
        # small suite runs; nothing is skipped), so we accept and document it.
        assert targets == sorted(
            [
                "tests/test_costs_alerts.py",
                "tests/test_costs_base.py",
                "tests/test_costs_cli.py",
                "tests/test_costs_providers.py",
                "tests/test_costs_provider_vercel.py",
                "tests/test_costs_registry.py",
                "tests/test_costs_wizard.py",
            ]
        )

    def test_secrets_package_uses_differently_named_suite(self) -> None:
        assert select("vibe/secrets/providers/fly.py") == ["tests/test_secrets_providers.py"]

    def test_git_package_maps_to_worktrees_suite(self) -> None:
        # The unit suite is always selected; the worktree↔state seam suite is
        # additive (see TestIntegrationSeams).
        assert "tests/test_git_worktrees.py" in select("vibe/git/worktrees.py")

    def test_integrations_package_maps_to_guardrail_and_shape_suites(self) -> None:
        assert select("vibe/integrations/pr_autopilot/__init__.py") == [
            "tests/test_integrations.py",
            "tests/test_integrations_guardrails.py",
        ]


class TestTopLevelModuleScoping:
    def test_top_level_module_maps_by_convention(self) -> None:
        assert select("vibe/update_check.py") == ["tests/test_update_check.py"]

    def test_main_module_maps_to_import_surface_suite(self) -> None:
        assert select("vibe/__main__.py") == ["tests/test_import_surface.py"]

    def test_top_level_module_without_tests_selects_nothing(self) -> None:
        # cors.py / github_actions.py have no unit suite; scoping to nothing is
        # fine because main runs the full suite as the backstop.
        assert select("vibe/cors.py") == []


class TestExplicitCrossFileMappings:
    def test_cli_main_pulls_pr_and_duplicate_suites(self) -> None:
        assert select("vibe/cli/main.py") == sorted(
            [
                "tests/test_cli_main_pr.py",
                "tests/test_cli_registry.py",
                "tests/test_duplicate_pr_prevention.py",
            ]
        )

    def test_cli_registry_maps_to_registry_suite(self) -> None:
        assert select("vibe/cli/registry.py") == ["tests/test_cli_registry.py"]

    def test_linear_change_includes_views(self) -> None:
        assert select("vibe/trackers/linear.py") == sorted(
            ["tests/test_trackers_linear.py", "tests/test_views.py"]
        )

    def test_wizard_costs_maps_to_costs_wizard_suite(self) -> None:
        assert select("vibe/wizards/costs.py") == ["tests/test_costs_wizard.py"]


class TestFailSafe:
    def test_unmapped_package_runs_everything(self) -> None:
        # A brand-new package with no convention-matching tests must fail safe.
        assert select("vibe/brandnew/thing.py") == RUN_ALL

    def test_changed_test_file_runs_itself(self) -> None:
        assert select("tests/test_doctor.py") == ["tests/test_doctor.py"]

    def test_docs_and_recipes_select_nothing(self) -> None:
        assert select("docs/cleanup/audit.md", "recipes/testing/modular-testing.md") == []

    def test_bin_changes_select_nothing(self) -> None:
        # bin/ wrappers are proven by the live smoke-test matrix, not pytest.
        assert select("bin/ticket") == []

    def test_empty_diff_selects_nothing(self) -> None:
        assert select() == []
        assert select("", "  ") == []


class TestIntegrationSeams:
    """A change to either side of a compose seam runs that seam's suite."""

    SEAM = "tests/integration/test_worktree_state.py"

    def test_worktrees_change_runs_seam_and_its_unit_suite(self) -> None:
        targets = select("vibe/git/worktrees.py")
        # The seam suite AND the package's own unit suite both run.
        assert self.SEAM in targets
        assert "tests/test_git_worktrees.py" in targets

    def test_state_change_runs_seam_and_its_unit_suite(self) -> None:
        targets = select("vibe/state.py")
        # state.py maps to duplicate_pr_prevention by SOURCE_TEST_MAP; the seam
        # is additive on top of that.
        assert self.SEAM in targets
        assert "tests/test_duplicate_pr_prevention.py" in targets

    def test_changed_integration_test_runs_itself(self) -> None:
        assert select(self.SEAM) == [self.SEAM]

    def test_unrelated_change_does_not_pull_in_seam(self) -> None:
        assert self.SEAM not in select("vibe/frontend/analyzer.py")

    def test_seam_appears_once_when_both_sides_change(self) -> None:
        targets = select("vibe/git/worktrees.py", "vibe/state.py")
        assert targets.count(self.SEAM) == 1


class TestScopeContract:
    """The promise VIBE-186 wires into `bin/ci-local --scope` and tests.yml:
    QA cost scales with blast radius. These assert the *property* (a one-module
    change runs a strict subset; a contract change runs everything), so a future
    edit to the mapping can't silently break the scaling guarantee."""

    def test_single_module_change_runs_strict_subset(self) -> None:
        # The worked example used in recipes/testing/modular-testing.md and the
        # PR: touching one module selects only its suites, never the whole tree.
        full = {f"tests/test_{stem}.py" for stem in KNOWN}
        targets = select("vibe/trackers/linear.py")
        assert targets != RUN_ALL
        assert set(targets) < full  # proper subset
        assert set(targets) == {"tests/test_trackers_linear.py", "tests/test_views.py"}

    def test_contract_file_change_runs_full_tree(self) -> None:
        # Cross-cutting / contract changes must still trigger full validation —
        # the rule the runner relies on to stay safe (documented in the recipe).
        assert select("vibe/config.py") == RUN_ALL
        assert select(".github/workflows/tests.yml") == RUN_ALL

    def test_docs_only_change_runs_no_python_tests(self) -> None:
        # A docs/recipe-only PR (like parts of this one) maps to no pytest target
        # — the runner skips pytest entirely rather than running the full suite.
        assert select("recipes/environments/cloud-bootstrap.md") == []

    def test_cli_discovers_repo_tests_from_package_root(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert testscope_main(["vibe/trackers/linear.py"]) == 0

        captured = capsys.readouterr()
        assert captured.out.strip() == "tests/test_trackers_linear.py tests/test_views.py"


class TestMappingIntegrity:
    def test_every_mapped_stem_exists_in_repo(self) -> None:
        """SOURCE_TEST_MAP must not reference test files that don't exist."""
        from pathlib import Path

        tests_dir = Path(__file__).resolve().parent
        real = discover_test_stems(tests_dir)
        mapped = {stem for stems in SOURCE_TEST_MAP.values() for stem in stems}
        missing = mapped - real
        assert not missing, f"SOURCE_TEST_MAP references nonexistent test suites: {sorted(missing)}"

    def test_dedupes_across_multiple_changed_files(self) -> None:
        targets = select("vibe/trackers/linear.py", "vibe/cli/ticket.py")
        # Both pull in views; it should appear once.
        assert targets.count("tests/test_views.py") == 1

    def test_every_seam_suite_file_exists(self) -> None:
        """INTEGRATION_SEAMS must not reference suites that don't exist."""
        from pathlib import Path

        repo_root = Path(__file__).resolve().parent.parent
        missing = [p for p in INTEGRATION_SEAMS if not (repo_root / p).exists()]
        assert not missing, f"INTEGRATION_SEAMS references nonexistent suites: {missing}"

    def test_every_seam_participant_is_a_source_path(self) -> None:
        """Seam participants must point at real package source under vibe/."""
        bad = [
            part
            for participants in INTEGRATION_SEAMS.values()
            for part in participants
            if not part.startswith("vibe/")
        ]
        assert not bad, f"seam participants must live under vibe/: {bad}"

    def test_each_seam_has_at_least_two_participants(self) -> None:
        """A 'seam' with one participant isn't a seam — it's a unit test."""
        thin = {p: parts for p, parts in INTEGRATION_SEAMS.items() if len(parts) < 2}
        assert not thin, f"integration seams need >=2 participants: {thin}"
