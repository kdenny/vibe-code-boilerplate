"""Unit tests for module-scoped test selection (lib/vibe/testscope.py)."""

from __future__ import annotations

import pytest

from lib.vibe.testscope import (
    RUN_ALL,
    SOURCE_TEST_MAP,
    discover_test_stems,
    select_test_targets,
)

# A representative slice of the real suite's stems. Kept explicit so the tests
# don't depend on the live tests/ directory contents.
KNOWN = {
    "config",
    "tools",
    "version",
    "update_check",
    "doctor",
    "label_sync",
    "cli_main_pr",
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
            "lib/vibe/__init__.py",
            "lib/vibe/config.py",
            "lib/vibe/config_schema.py",
            "lib/vibe/env.py",
            "lib/vibe/utils/cache.py",
            "lib/vibe/testscope.py",
            ".github/workflows/tests.yml",
        ],
    )
    def test_shared_path_forces_full_suite(self, path: str) -> None:
        assert select(path) == RUN_ALL

    def test_shared_path_wins_even_alongside_scoped_change(self) -> None:
        # If anything shared changed, the whole suite runs regardless of what
        # else is in the diff.
        assert select("lib/vibe/costs/providers/vercel.py", "pyproject.toml") == RUN_ALL


class TestPackageScoping:
    def test_costs_package_selects_all_costs_suites(self) -> None:
        targets = select("lib/vibe/costs/providers/vercel.py")
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
        assert select("lib/vibe/secrets/providers/fly.py") == ["tests/test_secrets_providers.py"]

    def test_git_package_maps_to_worktrees_suite(self) -> None:
        assert select("lib/vibe/git/worktrees.py") == ["tests/test_git_worktrees.py"]


class TestTopLevelModuleScoping:
    def test_top_level_module_maps_by_convention(self) -> None:
        assert select("lib/vibe/update_check.py") == ["tests/test_update_check.py"]

    def test_top_level_module_without_tests_selects_nothing(self) -> None:
        # cors.py / github_actions.py have no unit suite; scoping to nothing is
        # fine because main runs the full suite as the backstop.
        assert select("lib/vibe/cors.py") == []


class TestExplicitCrossFileMappings:
    def test_cli_main_pulls_pr_and_duplicate_suites(self) -> None:
        assert select("lib/vibe/cli/main.py") == sorted(
            ["tests/test_cli_main_pr.py", "tests/test_duplicate_pr_prevention.py"]
        )

    def test_linear_change_includes_views(self) -> None:
        assert select("lib/vibe/trackers/linear.py") == sorted(
            ["tests/test_trackers_linear.py", "tests/test_views.py"]
        )

    def test_wizard_costs_maps_to_costs_wizard_suite(self) -> None:
        assert select("lib/vibe/wizards/costs.py") == ["tests/test_costs_wizard.py"]


class TestFailSafe:
    def test_unmapped_package_runs_everything(self) -> None:
        # A brand-new package with no convention-matching tests must fail safe.
        assert select("lib/vibe/brandnew/thing.py") == RUN_ALL

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
        targets = select("lib/vibe/trackers/linear.py", "lib/vibe/cli/ticket.py")
        # Both pull in views; it should appear once.
        assert targets.count("tests/test_views.py") == 1
