"""Detection utilities for analyzing existing projects."""

import json
import re
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class DetectionResult:
    """Result of a detection operation."""

    detected: bool
    confidence: float  # 0.0 to 1.0
    value: Any = None
    details: str = ""


@dataclass
class ProjectProfile:
    """Profile of an existing project's configuration and patterns."""

    # Git configuration
    main_branch: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    branch_pattern: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    has_worktrees: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))

    # Package management
    package_manager: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    python_version: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))

    # Frameworks and libraries
    frontend_framework: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    backend_framework: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    css_framework: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))

    # Deployment and hosting
    vercel_config: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    fly_config: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    docker_config: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))

    # Database
    supabase_config: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    neon_config: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    database_type: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))

    # Testing
    test_framework: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))

    # CI/CD
    github_actions: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    has_pr_template: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))

    # Ticket tracking
    linear_integration: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))
    shortcut_integration: DetectionResult = field(
        default_factory=lambda: DetectionResult(False, 0.0)
    )

    # Existing vibe config
    has_vibe_config: DetectionResult = field(default_factory=lambda: DetectionResult(False, 0.0))


class ProjectDetector:
    """Detects existing project configuration and patterns."""

    def __init__(self, project_path: Path | None = None):
        """Initialize detector with project path."""
        self.project_path = project_path or Path.cwd()

    def detect_all(self) -> ProjectProfile:
        """Run all detection routines and return a complete profile."""
        profile = ProjectProfile()

        # Git detection
        profile.main_branch = self.detect_main_branch()
        profile.branch_pattern = self.detect_branch_pattern()
        profile.has_worktrees = self.detect_worktrees()

        # Package management
        profile.package_manager = self.detect_package_manager()
        profile.python_version = self.detect_python_version()

        # Frameworks
        profile.frontend_framework = self.detect_frontend_framework()
        profile.backend_framework = self.detect_backend_framework()
        profile.css_framework = self.detect_css_framework()

        # Deployment
        profile.vercel_config = self.detect_vercel()
        profile.fly_config = self.detect_fly()
        profile.docker_config = self.detect_docker()

        # Database
        profile.supabase_config = self.detect_supabase()
        profile.neon_config = self.detect_neon()
        profile.database_type = self.detect_database_type()

        # Testing
        profile.test_framework = self.detect_test_framework()

        # CI/CD
        profile.github_actions = self.detect_github_actions()
        profile.has_pr_template = self.detect_pr_template()

        # Ticket tracking
        profile.linear_integration = self.detect_linear()
        profile.shortcut_integration = self.detect_shortcut()

        # Existing vibe config
        profile.has_vibe_config = self.detect_vibe_config()

        return profile

    def detect_main_branch(self) -> DetectionResult:
        """Detect the main branch (main vs master)."""
        try:
            # First try symbolic-ref for HEAD
            result = subprocess.run(
                ["git", "-C", str(self.project_path), "symbolic-ref", "refs/remotes/origin/HEAD"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                ref = result.stdout.strip()
                branch = ref.split("/")[-1]
                return DetectionResult(True, 1.0, branch, f"Detected from origin/HEAD: {branch}")

            # Fallback: check if main or master exists
            result = subprocess.run(
                ["git", "-C", str(self.project_path), "branch", "-r"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                branches = result.stdout
                if "origin/main" in branches:
                    return DetectionResult(True, 0.9, "main", "Found origin/main remote branch")
                if "origin/master" in branches:
                    return DetectionResult(True, 0.9, "master", "Found origin/master remote branch")

            # Check local branches
            result = subprocess.run(
                ["git", "-C", str(self.project_path), "branch"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                branches = result.stdout
                if "main" in branches:
                    return DetectionResult(True, 0.8, "main", "Found local main branch")
                if "master" in branches:
                    return DetectionResult(True, 0.8, "master", "Found local master branch")

        except FileNotFoundError:
            pass  # git not installed

        return DetectionResult(False, 0.0, "main", "Could not detect main branch, defaulting")

    def detect_branch_pattern(self) -> DetectionResult:
        """Detect branch naming patterns from existing branches."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.project_path), "branch", "-a"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return DetectionResult(False, 0.0)

            branches = [
                b.strip().lstrip("* ").replace("remotes/origin/", "")
                for b in result.stdout.strip().split("\n")
                if b.strip() and "HEAD" not in b
            ]

            # Remove main/master from analysis
            branches = [b for b in branches if b not in ("main", "master", "develop", "dev")]

            if not branches:
                return DetectionResult(False, 0.0, None, "No feature branches found")

            # Pattern detection
            patterns: Counter[str] = Counter()

            for branch in branches:
                # Check for ticket ID patterns
                if re.match(r"^[A-Z]+-\d+", branch):
                    patterns["{PROJ}-{num}"] += 1
                elif re.match(r"^[a-z]+-\d+", branch):
                    patterns["{proj}-{num}"] += 1
                elif re.match(r"^(feature|fix|chore)/[A-Z]+-\d+", branch):
                    patterns["{type}/{PROJ}-{num}"] += 1
                elif re.match(r"^(feature|fix|chore)/", branch):
                    patterns["{type}/{description}"] += 1
                elif re.match(r"^\d+-", branch):
                    patterns["{num}-{description}"] += 1

            if patterns:
                most_common = patterns.most_common(1)[0]
                pattern, count = most_common
                confidence = min(count / len(branches), 1.0) if branches else 0.0
                return DetectionResult(
                    True,
                    confidence,
                    pattern,
                    f"Detected pattern '{pattern}' from {count}/{len(branches)} branches",
                )

            return DetectionResult(False, 0.3, "{PROJ}-{num}", "No clear pattern, suggesting default")

        except FileNotFoundError:
            return DetectionResult(False, 0.0)

    def detect_worktrees(self) -> DetectionResult:
        """Detect if project already uses git worktrees."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.project_path), "worktree", "list"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                worktrees = [
                    line for line in result.stdout.strip().split("\n") if line and "(bare)" not in line
                ]
                # More than just the main checkout means worktrees are in use
                if len(worktrees) > 1:
                    return DetectionResult(
                        True, 1.0, len(worktrees), f"Found {len(worktrees)} active worktrees"
                    )
                return DetectionResult(
                    False, 0.0, 1, "Only main checkout found (no additional worktrees)"
                )
        except FileNotFoundError:
            pass
        return DetectionResult(False, 0.0)

    def detect_package_manager(self) -> DetectionResult:
        """Detect Python package manager (poetry, pipenv, pip, uv)."""
        # Check for uv
        if (self.project_path / "uv.lock").exists():
            return DetectionResult(True, 1.0, "uv", "Found uv.lock")

        # Check for Poetry
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.poetry]" in content:
                return DetectionResult(True, 1.0, "poetry", "Found [tool.poetry] in pyproject.toml")

        # Check for Pipenv
        if (self.project_path / "Pipfile").exists():
            return DetectionResult(True, 1.0, "pipenv", "Found Pipfile")

        # Check for requirements.txt (pip)
        if (self.project_path / "requirements.txt").exists():
            return DetectionResult(True, 0.8, "pip", "Found requirements.txt")

        # pyproject.toml without poetry (could be pip with pyproject)
        if pyproject.exists():
            return DetectionResult(True, 0.7, "pip", "Found pyproject.toml (pip-compatible)")

        return DetectionResult(False, 0.0)

    def detect_python_version(self) -> DetectionResult:
        """Detect Python version from project configuration."""
        # Check .python-version
        pyversion_file = self.project_path / ".python-version"
        if pyversion_file.exists():
            version = pyversion_file.read_text().strip()
            return DetectionResult(True, 1.0, version, "Found .python-version")

        # Check pyproject.toml
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'python\s*[=<>]+\s*["\']?(\d+\.\d+)', content)
            if match:
                return DetectionResult(
                    True, 0.9, match.group(1), "Detected from pyproject.toml"
                )

        # Check runtime.txt (Heroku-style)
        runtime = self.project_path / "runtime.txt"
        if runtime.exists():
            content = runtime.read_text()
            match = re.search(r"python-(\d+\.\d+)", content)
            if match:
                return DetectionResult(True, 0.9, match.group(1), "Found runtime.txt")

        return DetectionResult(False, 0.0)

    def detect_frontend_framework(self) -> DetectionResult:
        """Detect frontend framework from package.json or config files."""
        package_json = self.project_path / "package.json"
        if not package_json.exists():
            return DetectionResult(False, 0.0)

        try:
            data = json.loads(package_json.read_text())
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

            # Check for frameworks (order matters - more specific first)
            if "next" in deps:
                return DetectionResult(True, 1.0, "next", "Found Next.js in dependencies")
            if "nuxt" in deps:
                return DetectionResult(True, 1.0, "nuxt", "Found Nuxt in dependencies")
            if "astro" in deps:
                return DetectionResult(True, 1.0, "astro", "Found Astro in dependencies")
            if "svelte" in deps or "@sveltejs/kit" in deps:
                return DetectionResult(True, 1.0, "svelte", "Found Svelte in dependencies")
            if "vue" in deps:
                return DetectionResult(True, 1.0, "vue", "Found Vue in dependencies")
            if "react" in deps:
                return DetectionResult(True, 1.0, "react", "Found React in dependencies")
            if "angular" in deps or "@angular/core" in deps:
                return DetectionResult(True, 1.0, "angular", "Found Angular in dependencies")

        except (json.JSONDecodeError, OSError):
            pass

        return DetectionResult(False, 0.0)

    def detect_backend_framework(self) -> DetectionResult:
        """Detect backend framework."""
        # Check pyproject.toml or requirements.txt for Python frameworks
        deps_text = ""
        pyproject = self.project_path / "pyproject.toml"
        requirements = self.project_path / "requirements.txt"

        if pyproject.exists():
            deps_text += pyproject.read_text().lower()
        if requirements.exists():
            deps_text += requirements.read_text().lower()

        if "fastapi" in deps_text:
            return DetectionResult(True, 1.0, "fastapi", "Found FastAPI in dependencies")
        if "django" in deps_text:
            return DetectionResult(True, 1.0, "django", "Found Django in dependencies")
        if "flask" in deps_text:
            return DetectionResult(True, 1.0, "flask", "Found Flask in dependencies")
        if "litestar" in deps_text:
            return DetectionResult(True, 1.0, "litestar", "Found Litestar in dependencies")

        # Check package.json for Node.js backends
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                if "express" in deps:
                    return DetectionResult(True, 1.0, "express", "Found Express in dependencies")
                if "fastify" in deps:
                    return DetectionResult(True, 1.0, "fastify", "Found Fastify in dependencies")
                if "hono" in deps:
                    return DetectionResult(True, 1.0, "hono", "Found Hono in dependencies")
            except (json.JSONDecodeError, OSError):
                pass

        return DetectionResult(False, 0.0)

    def detect_css_framework(self) -> DetectionResult:
        """Detect CSS framework."""
        # Check for Tailwind config
        if (self.project_path / "tailwind.config.js").exists() or (
            self.project_path / "tailwind.config.ts"
        ).exists():
            return DetectionResult(True, 1.0, "tailwind", "Found tailwind.config")

        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                if "tailwindcss" in deps:
                    return DetectionResult(True, 1.0, "tailwind", "Found Tailwind in dependencies")
                if "@chakra-ui/react" in deps:
                    return DetectionResult(True, 1.0, "chakra", "Found Chakra UI in dependencies")
                if "@mui/material" in deps:
                    return DetectionResult(True, 1.0, "mui", "Found MUI in dependencies")
                if "bootstrap" in deps:
                    return DetectionResult(True, 1.0, "bootstrap", "Found Bootstrap in dependencies")

            except (json.JSONDecodeError, OSError):
                pass

        return DetectionResult(False, 0.0)

    def detect_vercel(self) -> DetectionResult:
        """Detect Vercel configuration."""
        vercel_json = self.project_path / "vercel.json"
        if vercel_json.exists():
            return DetectionResult(True, 1.0, "configured", "Found vercel.json")

        # Check for .vercel directory
        if (self.project_path / ".vercel").is_dir():
            return DetectionResult(True, 0.9, "linked", "Found .vercel directory (project linked)")

        return DetectionResult(False, 0.0)

    def detect_fly(self) -> DetectionResult:
        """Detect Fly.io configuration."""
        fly_toml = self.project_path / "fly.toml"
        if fly_toml.exists():
            return DetectionResult(True, 1.0, "configured", "Found fly.toml")

        return DetectionResult(False, 0.0)

    def detect_docker(self) -> DetectionResult:
        """Detect Docker configuration."""
        dockerfile = self.project_path / "Dockerfile"
        compose = self.project_path / "docker-compose.yml"
        compose_yaml = self.project_path / "docker-compose.yaml"

        configs_found = []
        if dockerfile.exists():
            configs_found.append("Dockerfile")
        if compose.exists() or compose_yaml.exists():
            configs_found.append("docker-compose")

        if configs_found:
            return DetectionResult(
                True, 1.0, configs_found, f"Found: {', '.join(configs_found)}"
            )

        return DetectionResult(False, 0.0)

    def detect_supabase(self) -> DetectionResult:
        """Detect Supabase configuration."""
        # Check for supabase directory (local dev)
        if (self.project_path / "supabase" / "config.toml").exists():
            return DetectionResult(True, 1.0, "local", "Found supabase/config.toml")

        # Check environment files for SUPABASE_URL
        env_files = [".env", ".env.local", ".env.example"]
        for env_file in env_files:
            env_path = self.project_path / env_file
            if env_path.exists():
                content = env_path.read_text()
                if "SUPABASE_URL" in content or "NEXT_PUBLIC_SUPABASE_URL" in content:
                    return DetectionResult(
                        True, 0.8, "env", f"Found Supabase config in {env_file}"
                    )

        return DetectionResult(False, 0.0)

    def detect_neon(self) -> DetectionResult:
        """Detect Neon database configuration."""
        env_files = [".env", ".env.local", ".env.example"]
        for env_file in env_files:
            env_path = self.project_path / env_file
            if env_path.exists():
                content = env_path.read_text()
                if "neon.tech" in content or "NEON_" in content:
                    return DetectionResult(True, 0.8, "env", f"Found Neon config in {env_file}")

        return DetectionResult(False, 0.0)

    def detect_database_type(self) -> DetectionResult:
        """Detect database type from configuration or dependencies."""
        # Check environment files
        env_files = [".env", ".env.local", ".env.example"]
        for env_file in env_files:
            env_path = self.project_path / env_file
            if env_path.exists():
                content = env_path.read_text().lower()
                if "postgres" in content or "postgresql" in content:
                    return DetectionResult(True, 0.8, "postgres", "Found PostgreSQL in env")
                if "mysql" in content:
                    return DetectionResult(True, 0.8, "mysql", "Found MySQL in env")
                if "mongodb" in content or "mongo_" in content:
                    return DetectionResult(True, 0.8, "mongodb", "Found MongoDB in env")
                if "redis" in content:
                    return DetectionResult(True, 0.8, "redis", "Found Redis in env")

        return DetectionResult(False, 0.0)

    def detect_test_framework(self) -> DetectionResult:
        """Detect test framework."""
        # Python test frameworks
        deps_text = ""
        pyproject = self.project_path / "pyproject.toml"
        requirements = self.project_path / "requirements.txt"

        if pyproject.exists():
            deps_text += pyproject.read_text().lower()
        if requirements.exists():
            deps_text += requirements.read_text().lower()

        if "pytest" in deps_text:
            return DetectionResult(True, 1.0, "pytest", "Found pytest in dependencies")

        # Check for pytest.ini or pyproject.toml [tool.pytest]
        if (self.project_path / "pytest.ini").exists():
            return DetectionResult(True, 1.0, "pytest", "Found pytest.ini")

        # JavaScript test frameworks
        package_json = self.project_path / "package.json"
        if package_json.exists():
            try:
                data = json.loads(package_json.read_text())
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}

                if "vitest" in deps:
                    return DetectionResult(True, 1.0, "vitest", "Found Vitest in dependencies")
                if "jest" in deps:
                    return DetectionResult(True, 1.0, "jest", "Found Jest in dependencies")
                if "@playwright/test" in deps:
                    return DetectionResult(True, 1.0, "playwright", "Found Playwright in deps")
                if "cypress" in deps:
                    return DetectionResult(True, 1.0, "cypress", "Found Cypress in dependencies")

            except (json.JSONDecodeError, OSError):
                pass

        return DetectionResult(False, 0.0)

    def detect_github_actions(self) -> DetectionResult:
        """Detect GitHub Actions workflows."""
        workflows_dir = self.project_path / ".github" / "workflows"
        if workflows_dir.is_dir():
            workflows = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
            if workflows:
                names = [w.stem for w in workflows]
                return DetectionResult(
                    True, 1.0, names, f"Found {len(workflows)} workflow(s): {', '.join(names)}"
                )

        return DetectionResult(False, 0.0)

    def detect_pr_template(self) -> DetectionResult:
        """Detect PR template."""
        templates = [
            self.project_path / ".github" / "PULL_REQUEST_TEMPLATE.md",
            self.project_path / ".github" / "pull_request_template.md",
            self.project_path / "PULL_REQUEST_TEMPLATE.md",
        ]

        for template in templates:
            if template.exists():
                return DetectionResult(True, 1.0, str(template), f"Found {template.name}")

        return DetectionResult(False, 0.0)

    def detect_linear(self) -> DetectionResult:
        """Detect Linear integration."""
        # Check for LINEAR_API_KEY in env files
        env_files = [".env", ".env.local", ".env.example"]
        for env_file in env_files:
            env_path = self.project_path / env_file
            if env_path.exists():
                content = env_path.read_text()
                if "LINEAR_API_KEY" in content or "LINEAR_" in content:
                    return DetectionResult(True, 0.8, "env", f"Found Linear config in {env_file}")

        # Check for Linear-style branch names
        branch_result = self.detect_branch_pattern()
        if branch_result.detected and branch_result.value in ("{PROJ}-{num}", "{type}/{PROJ}-{num}"):
            return DetectionResult(
                True, 0.6, "branch-pattern", "Branch pattern suggests Linear-style tickets"
            )

        return DetectionResult(False, 0.0)

    def detect_shortcut(self) -> DetectionResult:
        """Detect Shortcut integration."""
        env_files = [".env", ".env.local", ".env.example"]
        for env_file in env_files:
            env_path = self.project_path / env_file
            if env_path.exists():
                content = env_path.read_text()
                if "SHORTCUT_API_TOKEN" in content or "CLUBHOUSE_" in content:
                    return DetectionResult(
                        True, 0.8, "env", f"Found Shortcut config in {env_file}"
                    )

        return DetectionResult(False, 0.0)

    def detect_vibe_config(self) -> DetectionResult:
        """Detect if project already has vibe configuration."""
        config_path = self.project_path / ".vibe" / "config.json"
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
                version = config.get("version", "unknown")
                return DetectionResult(
                    True, 1.0, version, f"Found .vibe/config.json (version {version})"
                )
            except (json.JSONDecodeError, OSError):
                return DetectionResult(True, 0.5, "invalid", "Found .vibe/config.json (invalid)")

        return DetectionResult(False, 0.0)
