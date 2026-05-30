"""Guardrails for publishable integration modules."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN_DOWNSTREAM_IMPORT_ROOTS = {
    "app",
    "apps",
    "backend",
    "deal",
    "frontend",
    "lift",
    "lift_with_lou",
    "nyc_re_tracker",
    "nyc_re_tracker_2",
    "server",
    "src",
}


def _forbidden_import_roots(source: str, filename: str = "<source>") -> list[str]:
    tree = ast.parse(source, filename=filename)
    forbidden: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in FORBIDDEN_DOWNSTREAM_IMPORT_ROOTS:
                    forbidden.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            root = node.module.split(".", 1)[0]
            if root in FORBIDDEN_DOWNSTREAM_IMPORT_ROOTS:
                forbidden.append(node.module)
    return forbidden


def test_integrations_do_not_import_downstream_app_code() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    integration_files = sorted((repo_root / "lib/vibe/integrations").rglob("*.py"))
    violations = {
        str(path.relative_to(repo_root)): _forbidden_import_roots(path.read_text(), str(path))
        for path in integration_files
    }
    violations = {path: imports for path, imports in violations.items() if imports}

    assert not violations, f"integration modules import downstream app code: {violations}"


def test_deliberate_app_code_import_is_caught() -> None:
    source = """
import app.models
from lift_with_lou.prs import runner
from lib.vibe.cli import Integration
"""

    assert _forbidden_import_roots(source) == ["app.models", "lift_with_lou.prs"]
