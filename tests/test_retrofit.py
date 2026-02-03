"""Tests for the retrofit module."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lib.vibe.retrofit.analyzer import (
    ActionPriority,
    ActionType,
    RetrofitAction,
    RetrofitAnalyzer,
    RetrofitPlan,
)
from lib.vibe.retrofit.applier import ApplyResult, RetrofitApplier
from lib.vibe.retrofit.detector import DetectionResult, ProjectDetector, ProjectProfile


class TestDetectionResult:
    """Tests for DetectionResult dataclass."""

    def test_basic_creation(self) -> None:
        """Test creating a basic detection result."""
        result = DetectionResult(True, 0.9, "test_value", "Test details")
        assert result.detected is True
        assert result.confidence == 0.9
        assert result.value == "test_value"
        assert result.details == "Test details"

    def test_default_values(self) -> None:
        """Test default values."""
        result = DetectionResult(False, 0.0)
        assert result.detected is False
        assert result.confidence == 0.0
        assert result.value is None
        assert result.details == ""


class TestProjectProfile:
    """Tests for ProjectProfile dataclass."""

    def test_default_profile(self) -> None:
        """Test creating a profile with defaults."""
        profile = ProjectProfile()
        assert profile.main_branch.detected is False
        assert profile.branch_pattern.detected is False
        assert profile.frontend_framework.detected is False


class TestProjectDetector:
    """Tests for ProjectDetector."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project = tmp_path / "test-project"
        project.mkdir()
        return project

    def test_init_default_path(self) -> None:
        """Test detector initializes with current directory."""
        detector = ProjectDetector()
        assert detector.project_path == Path.cwd()

    def test_init_custom_path(self, temp_project: Path) -> None:
        """Test detector initializes with custom path."""
        detector = ProjectDetector(temp_project)
        assert detector.project_path == temp_project

    def test_detect_main_branch_from_origin_head(self, temp_project: Path) -> None:
        """Test detecting main branch from origin/HEAD."""
        detector = ProjectDetector(temp_project)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="refs/remotes/origin/main\n"
            )
            result = detector.detect_main_branch()
            assert result.detected is True
            assert result.value == "main"
            assert result.confidence == 1.0

    def test_detect_main_branch_fallback_to_remote(self, temp_project: Path) -> None:
        """Test detecting main branch from remote branches."""
        detector = ProjectDetector(temp_project)
        with patch("subprocess.run") as mock_run:
            # First call (symbolic-ref) fails, second (branch -r) succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout=""),
                MagicMock(returncode=0, stdout="  origin/main\n  origin/feature-1\n"),
            ]
            result = detector.detect_main_branch()
            assert result.detected is True
            assert result.value == "main"
            assert result.confidence == 0.9

    def test_detect_main_branch_master(self, temp_project: Path) -> None:
        """Test detecting master as main branch."""
        detector = ProjectDetector(temp_project)
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = [
                MagicMock(returncode=1, stdout=""),
                MagicMock(returncode=0, stdout="  origin/master\n"),
            ]
            result = detector.detect_main_branch()
            assert result.detected is True
            assert result.value == "master"

    def test_detect_branch_pattern_proj_num(self, temp_project: Path) -> None:
        """Test detecting {PROJ}-{num} pattern."""
        detector = ProjectDetector(temp_project)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  main\n  TEST-1\n  TEST-2\n  TEST-3\n  TEST-4-feature\n",
            )
            result = detector.detect_branch_pattern()
            assert result.detected is True
            assert result.value == "{PROJ}-{num}"
            assert result.confidence >= 0.75

    def test_detect_branch_pattern_no_branches(self, temp_project: Path) -> None:
        """Test detecting pattern with no feature branches."""
        detector = ProjectDetector(temp_project)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="  main\n")
            result = detector.detect_branch_pattern()
            assert result.detected is False

    def test_detect_package_manager_poetry(self, temp_project: Path) -> None:
        """Test detecting Poetry package manager."""
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "test"')
        detector = ProjectDetector(temp_project)
        result = detector.detect_package_manager()
        assert result.detected is True
        assert result.value == "poetry"
        assert result.confidence == 1.0

    def test_detect_package_manager_pipenv(self, temp_project: Path) -> None:
        """Test detecting Pipenv package manager."""
        pipfile = temp_project / "Pipfile"
        pipfile.write_text("[packages]")
        detector = ProjectDetector(temp_project)
        result = detector.detect_package_manager()
        assert result.detected is True
        assert result.value == "pipenv"

    def test_detect_package_manager_pip(self, temp_project: Path) -> None:
        """Test detecting pip from requirements.txt."""
        requirements = temp_project / "requirements.txt"
        requirements.write_text("click==8.0.0")
        detector = ProjectDetector(temp_project)
        result = detector.detect_package_manager()
        assert result.detected is True
        assert result.value == "pip"

    def test_detect_package_manager_uv(self, temp_project: Path) -> None:
        """Test detecting uv package manager."""
        uv_lock = temp_project / "uv.lock"
        uv_lock.write_text("version = 1")
        detector = ProjectDetector(temp_project)
        result = detector.detect_package_manager()
        assert result.detected is True
        assert result.value == "uv"

    def test_detect_frontend_framework_next(self, temp_project: Path) -> None:
        """Test detecting Next.js."""
        package_json = temp_project / "package.json"
        package_json.write_text(json.dumps({"dependencies": {"next": "14.0.0"}}))
        detector = ProjectDetector(temp_project)
        result = detector.detect_frontend_framework()
        assert result.detected is True
        assert result.value == "next"

    def test_detect_frontend_framework_react(self, temp_project: Path) -> None:
        """Test detecting React."""
        package_json = temp_project / "package.json"
        package_json.write_text(json.dumps({"dependencies": {"react": "18.0.0"}}))
        detector = ProjectDetector(temp_project)
        result = detector.detect_frontend_framework()
        assert result.detected is True
        assert result.value == "react"

    def test_detect_backend_framework_fastapi(self, temp_project: Path) -> None:
        """Test detecting FastAPI."""
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["fastapi"]')
        detector = ProjectDetector(temp_project)
        result = detector.detect_backend_framework()
        assert result.detected is True
        assert result.value == "fastapi"

    def test_detect_backend_framework_django(self, temp_project: Path) -> None:
        """Test detecting Django."""
        requirements = temp_project / "requirements.txt"
        requirements.write_text("Django>=4.0")
        detector = ProjectDetector(temp_project)
        result = detector.detect_backend_framework()
        assert result.detected is True
        assert result.value == "django"

    def test_detect_css_framework_tailwind(self, temp_project: Path) -> None:
        """Test detecting Tailwind CSS."""
        tailwind_config = temp_project / "tailwind.config.js"
        tailwind_config.write_text("module.exports = {}")
        detector = ProjectDetector(temp_project)
        result = detector.detect_css_framework()
        assert result.detected is True
        assert result.value == "tailwind"

    def test_detect_vercel(self, temp_project: Path) -> None:
        """Test detecting Vercel configuration."""
        vercel_json = temp_project / "vercel.json"
        vercel_json.write_text("{}")
        detector = ProjectDetector(temp_project)
        result = detector.detect_vercel()
        assert result.detected is True
        assert result.value == "configured"

    def test_detect_fly(self, temp_project: Path) -> None:
        """Test detecting Fly.io configuration."""
        fly_toml = temp_project / "fly.toml"
        fly_toml.write_text("[env]")
        detector = ProjectDetector(temp_project)
        result = detector.detect_fly()
        assert result.detected is True
        assert result.value == "configured"

    def test_detect_docker(self, temp_project: Path) -> None:
        """Test detecting Docker configuration."""
        dockerfile = temp_project / "Dockerfile"
        dockerfile.write_text("FROM python:3.11")
        detector = ProjectDetector(temp_project)
        result = detector.detect_docker()
        assert result.detected is True
        assert "Dockerfile" in result.value

    def test_detect_supabase(self, temp_project: Path) -> None:
        """Test detecting Supabase configuration."""
        supabase_dir = temp_project / "supabase"
        supabase_dir.mkdir()
        (supabase_dir / "config.toml").write_text("[api]")
        detector = ProjectDetector(temp_project)
        result = detector.detect_supabase()
        assert result.detected is True
        assert result.value == "local"

    def test_detect_supabase_from_env(self, temp_project: Path) -> None:
        """Test detecting Supabase from environment file."""
        env = temp_project / ".env.example"
        env.write_text("SUPABASE_URL=https://xxx.supabase.co")
        detector = ProjectDetector(temp_project)
        result = detector.detect_supabase()
        assert result.detected is True
        assert result.value == "env"

    def test_detect_test_framework_pytest(self, temp_project: Path) -> None:
        """Test detecting pytest."""
        pyproject = temp_project / "pyproject.toml"
        pyproject.write_text('[project]\ndependencies = ["pytest"]')
        detector = ProjectDetector(temp_project)
        result = detector.detect_test_framework()
        assert result.detected is True
        assert result.value == "pytest"

    def test_detect_test_framework_vitest(self, temp_project: Path) -> None:
        """Test detecting Vitest."""
        package_json = temp_project / "package.json"
        package_json.write_text(json.dumps({"devDependencies": {"vitest": "1.0.0"}}))
        detector = ProjectDetector(temp_project)
        result = detector.detect_test_framework()
        assert result.detected is True
        assert result.value == "vitest"

    def test_detect_github_actions(self, temp_project: Path) -> None:
        """Test detecting GitHub Actions workflows."""
        workflows_dir = temp_project / ".github" / "workflows"
        workflows_dir.mkdir(parents=True)
        (workflows_dir / "ci.yml").write_text("name: CI")
        (workflows_dir / "deploy.yml").write_text("name: Deploy")
        detector = ProjectDetector(temp_project)
        result = detector.detect_github_actions()
        assert result.detected is True
        assert len(result.value) == 2
        assert "ci" in result.value
        assert "deploy" in result.value

    def test_detect_pr_template(self, temp_project: Path) -> None:
        """Test detecting PR template."""
        github_dir = temp_project / ".github"
        github_dir.mkdir()
        (github_dir / "PULL_REQUEST_TEMPLATE.md").write_text("## Summary")
        detector = ProjectDetector(temp_project)
        result = detector.detect_pr_template()
        assert result.detected is True

    def test_detect_vibe_config(self, temp_project: Path) -> None:
        """Test detecting existing vibe configuration."""
        vibe_dir = temp_project / ".vibe"
        vibe_dir.mkdir()
        config = vibe_dir / "config.json"
        config.write_text(json.dumps({"version": "1.0.0"}))
        detector = ProjectDetector(temp_project)
        result = detector.detect_vibe_config()
        assert result.detected is True
        assert result.value == "1.0.0"

    def test_detect_linear(self, temp_project: Path) -> None:
        """Test detecting Linear integration."""
        env = temp_project / ".env.local"
        env.write_text("LINEAR_API_KEY=lin_api_xxx")
        detector = ProjectDetector(temp_project)
        result = detector.detect_linear()
        assert result.detected is True
        assert result.value == "env"


class TestRetrofitAnalyzer:
    """Tests for RetrofitAnalyzer."""

    def test_analyze_empty_profile(self) -> None:
        """Test analyzing an empty profile."""
        profile = ProjectProfile()
        analyzer = RetrofitAnalyzer(profile)
        plan = analyzer.analyze()
        assert len(plan.actions) > 0
        # Should have vibe_config as ADOPT
        vibe_action = next(a for a in plan.actions if a.name == "vibe_config")
        assert vibe_action.action_type == ActionType.ADOPT

    def test_analyze_with_vibe_config(self) -> None:
        """Test analyzing profile with existing vibe config."""
        profile = ProjectProfile()
        profile.has_vibe_config = DetectionResult(True, 1.0, "1.0.0", "Found config")
        analyzer = RetrofitAnalyzer(profile)
        plan = analyzer.analyze()
        vibe_action = next(a for a in plan.actions if a.name == "vibe_config")
        assert vibe_action.action_type == ActionType.SKIP

    def test_analyze_main_branch_detected(self) -> None:
        """Test analyzing with detected main branch."""
        profile = ProjectProfile()
        profile.main_branch = DetectionResult(True, 1.0, "main", "Detected")
        analyzer = RetrofitAnalyzer(profile)
        plan = analyzer.analyze()
        main_action = next(a for a in plan.actions if a.name == "main_branch")
        assert main_action.action_type == ActionType.CONFIGURE
        assert main_action.suggested_value == "main"

    def test_analyze_unusual_main_branch(self) -> None:
        """Test analyzing with unusual main branch."""
        profile = ProjectProfile()
        profile.main_branch = DetectionResult(True, 1.0, "develop", "Detected")
        analyzer = RetrofitAnalyzer(profile)
        plan = analyzer.analyze()
        main_action = next(a for a in plan.actions if a.name == "main_branch")
        assert main_action.action_type == ActionType.CONFLICT

    def test_analyze_branch_pattern_high_confidence(self) -> None:
        """Test analyzing high-confidence branch pattern."""
        profile = ProjectProfile()
        profile.branch_pattern = DetectionResult(True, 0.9, "{PROJ}-{num}", "90% conf")
        analyzer = RetrofitAnalyzer(profile)
        plan = analyzer.analyze()
        pattern_action = next(a for a in plan.actions if a.name == "branch_pattern")
        assert pattern_action.action_type == ActionType.CONFIGURE
        assert pattern_action.auto_applicable is True

    def test_analyze_branch_pattern_low_confidence(self) -> None:
        """Test analyzing low-confidence branch pattern."""
        profile = ProjectProfile()
        profile.branch_pattern = DetectionResult(True, 0.4, "{type}/{desc}", "40% conf")
        analyzer = RetrofitAnalyzer(profile)
        plan = analyzer.analyze()
        pattern_action = next(a for a in plan.actions if a.name == "branch_pattern")
        assert pattern_action.action_type == ActionType.CONFIGURE
        assert pattern_action.auto_applicable is False

    def test_generate_summary(self) -> None:
        """Test generating human-readable summary."""
        profile = ProjectProfile()
        profile.main_branch = DetectionResult(True, 1.0, "main", "Detected")
        profile.frontend_framework = DetectionResult(True, 1.0, "next", "Found Next.js")
        analyzer = RetrofitAnalyzer(profile)
        plan = analyzer.analyze()
        summary = analyzer.generate_summary(plan)
        assert "Retrofit Analysis Summary" in summary
        assert "Main branch: main" in summary
        assert "Frontend: next" in summary


class TestRetrofitPlan:
    """Tests for RetrofitPlan."""

    def test_required_actions(self) -> None:
        """Test filtering required actions."""
        plan = RetrofitPlan()
        plan.actions = [
            RetrofitAction("a", ActionType.ADOPT, ActionPriority.REQUIRED, "Required"),
            RetrofitAction("b", ActionType.ADOPT, ActionPriority.RECOMMENDED, "Recommended"),
        ]
        assert len(plan.required_actions) == 1
        assert plan.required_actions[0].name == "a"

    def test_conflicts(self) -> None:
        """Test filtering conflicts."""
        plan = RetrofitPlan()
        plan.actions = [
            RetrofitAction("a", ActionType.CONFLICT, ActionPriority.REQUIRED, "Conflict"),
            RetrofitAction("b", ActionType.ADOPT, ActionPriority.REQUIRED, "Normal"),
        ]
        assert len(plan.conflicts) == 1
        assert plan.conflicts[0].name == "a"

    def test_auto_applicable_actions(self) -> None:
        """Test filtering auto-applicable actions."""
        plan = RetrofitPlan()
        plan.actions = [
            RetrofitAction(
                "a", ActionType.ADOPT, ActionPriority.REQUIRED, "Auto", auto_applicable=True
            ),
            RetrofitAction(
                "b", ActionType.ADOPT, ActionPriority.REQUIRED, "Manual", auto_applicable=False
            ),
            RetrofitAction(
                "c", ActionType.SKIP, ActionPriority.OPTIONAL, "Skip", auto_applicable=True
            ),
        ]
        auto = plan.auto_applicable_actions
        assert len(auto) == 1
        assert auto[0].name == "a"


class TestRetrofitApplier:
    """Tests for RetrofitApplier."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path) -> Path:
        """Create a temporary project directory."""
        project = tmp_path / "test-project"
        project.mkdir()
        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project, capture_output=True)
        return project

    def test_init_defaults(self) -> None:
        """Test applier initializes with defaults."""
        applier = RetrofitApplier()
        assert applier.project_path == Path.cwd()
        assert applier.dry_run is False

    def test_dry_run_vibe_config(self, temp_project: Path) -> None:
        """Test dry run doesn't create files."""
        applier = RetrofitApplier(project_path=temp_project, dry_run=True)
        action = RetrofitAction(
            "vibe_config", ActionType.ADOPT, ActionPriority.REQUIRED, "Create config"
        )
        result = applier.apply_action(action)
        assert result.success is True
        assert "Would create" in result.message
        assert not (temp_project / ".vibe" / "config.json").exists()

    def test_apply_vibe_config(self, temp_project: Path) -> None:
        """Test applying vibe config."""
        applier = RetrofitApplier(project_path=temp_project)
        action = RetrofitAction(
            "vibe_config", ActionType.ADOPT, ActionPriority.REQUIRED, "Create config"
        )
        result = applier.apply_action(action)
        assert result.success is True
        assert (temp_project / ".vibe" / "config.json").exists()
        assert (temp_project / ".vibe" / "local_state.json").exists()

    def test_apply_main_branch(self, temp_project: Path) -> None:
        """Test applying main branch config."""
        # Create initial config
        vibe_dir = temp_project / ".vibe"
        vibe_dir.mkdir()
        (vibe_dir / "config.json").write_text('{"version": "1.0.0"}')

        applier = RetrofitApplier(project_path=temp_project)
        action = RetrofitAction(
            "main_branch",
            ActionType.CONFIGURE,
            ActionPriority.REQUIRED,
            "Set main branch",
            suggested_value="main",
        )
        result = applier.apply_action(action)
        assert result.success is True

        # Verify config was updated
        config = json.loads((vibe_dir / "config.json").read_text())
        assert config["branching"]["main_branch"] == "main"

    def test_apply_pr_template(self, temp_project: Path) -> None:
        """Test applying PR template."""
        applier = RetrofitApplier(project_path=temp_project)
        action = RetrofitAction(
            "pr_template", ActionType.ADOPT, ActionPriority.RECOMMENDED, "Create PR template"
        )
        result = applier.apply_action(action)
        assert result.success is True

        template_path = temp_project / ".github" / "PULL_REQUEST_TEMPLATE.md"
        assert template_path.exists()
        assert "Risk Assessment" in template_path.read_text()

    def test_apply_pr_template_already_exists(self, temp_project: Path) -> None:
        """Test PR template not overwritten if exists."""
        github_dir = temp_project / ".github"
        github_dir.mkdir()
        template_path = github_dir / "PULL_REQUEST_TEMPLATE.md"
        template_path.write_text("# Custom Template")

        applier = RetrofitApplier(project_path=temp_project)
        action = RetrofitAction(
            "pr_template", ActionType.ADOPT, ActionPriority.RECOMMENDED, "Create PR template"
        )
        result = applier.apply_action(action)
        assert result.success is True
        assert "already exists" in result.message
        assert template_path.read_text() == "# Custom Template"

    def test_apply_unknown_action(self, temp_project: Path) -> None:
        """Test applying unknown action fails gracefully."""
        applier = RetrofitApplier(project_path=temp_project)
        action = RetrofitAction(
            "unknown_action", ActionType.ADOPT, ActionPriority.OPTIONAL, "Unknown"
        )
        result = applier.apply_action(action)
        assert result.success is False
        assert "No applier found" in result.message

    def test_apply_plan_auto_only(self, temp_project: Path) -> None:
        """Test applying plan with auto_only=True."""
        applier = RetrofitApplier(project_path=temp_project)
        plan = RetrofitPlan()
        plan.actions = [
            RetrofitAction(
                "vibe_config",
                ActionType.ADOPT,
                ActionPriority.REQUIRED,
                "Create config",
                auto_applicable=True,
            ),
            RetrofitAction(
                "manual_action",
                ActionType.ADOPT,
                ActionPriority.REQUIRED,
                "Manual",
                auto_applicable=False,
            ),
        ]

        results = applier.apply_plan(plan, auto_only=True, interactive=False)
        assert len(results) == 1
        assert results[0].action_name == "vibe_config"

    def test_apply_github_actions_minimal(self, temp_project: Path) -> None:
        """Test applying minimal GitHub Actions workflows."""
        applier = RetrofitApplier(project_path=temp_project)
        action = RetrofitAction(
            "github_actions",
            ActionType.ADOPT,
            ActionPriority.RECOMMENDED,
            "Add workflows",
        )
        result = applier.apply_action(action)
        assert result.success is True

        workflows_dir = temp_project / ".github" / "workflows"
        assert workflows_dir.exists()
        assert (workflows_dir / "pr-policy.yml").exists()
        assert (workflows_dir / "security.yml").exists()
