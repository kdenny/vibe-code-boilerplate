"""Module-scoped test selection for fast, modular CI.

Given the set of files changed in a pull request, decide which pytest targets
to run. The goal is the **speed rule** from CLAUDE.md: a PR that touches one
module should only run that module's unit tests, not the whole suite. The full
suite still runs on ``main`` (the safety net) and whenever a shared/core file
changes (where the blast radius is the whole package).

Design contract:

- **Fail safe, not fast.** When a changed path under ``lib/vibe/`` has no known
  test mapping, we return :data:`RUN_ALL` rather than silently skipping it. A
  forgotten mapping costs a slower CI run, never a missed regression.
- **main is the backstop.** PR runs are scoped for fast feedback; ``main`` runs
  the full suite before anything is released. A cross-module dependency that a
  scoped PR run misses is caught on ``main`` before it ships. This tradeoff is
  intentional and is why the mapping does not try to be exhaustive about
  transitive coupling.
- **One module = one mapping entry.** :data:`SOURCE_TEST_MAP` doubles as the
  living map of which test files cover which module. Keep it in sync when you
  add a module or a test file (``test_testscope.py`` enforces that the mapped
  stems exist).

The mapping is convention-led: ``lib/vibe/<pkg>/`` is covered by every
``tests/test_<pkg>_*.py`` plus ``tests/test_<pkg>.py``, and a top-level
``lib/vibe/<name>.py`` is covered by ``tests/test_<name>.py``. The explicit
entries below only exist where that convention does not hold (e.g. the views
feature lives in ``trackers/linear.py`` but is tested in ``test_views.py``).

Two test *levels* exist (see ``recipes/testing/modular-testing.md``):

- **Unit** — one module in isolation, ``tests/test_<module>.py``. Selected by
  the convention + :data:`SOURCE_TEST_MAP` above.
- **Integration** — a real compose *seam* between modules, under
  ``tests/integration/``. Selected by :data:`INTEGRATION_SEAMS`: a change to
  *any* participant of a seam runs that seam's suite, on top of the
  participants' own unit tests. Seams are added only where modules are designed
  to compose in the product — not for every pair that merely imports another.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable
from pathlib import Path

# Sentinel returned (and printed) when the full suite must run.
RUN_ALL = "ALL"

# Changing any of these forces the full suite: they are imported across the
# whole package, so their blast radius is everything.
SHARED_PREFIXES: tuple[str, ...] = (
    "pyproject.toml",
    "tests/conftest.py",
    "tests/__init__.py",
    "lib/vibe/__init__.py",
    "lib/vibe/config.py",
    "lib/vibe/config_schema.py",
    "lib/vibe/env.py",
    "lib/vibe/utils/",
    # The CI plumbing itself — if the selector or the workflow changes, run
    # everything so the change is validated against the whole suite.
    "lib/vibe/testscope.py",
    ".github/workflows/tests.yml",
)

# Explicit source-path -> test-file-stem mappings for cases where the naming
# convention does not connect them. A key ending in "/" matches by prefix
# (a whole package); otherwise it matches an exact file path. Stems are the
# part after ``tests/test_`` and before ``.py``.
SOURCE_TEST_MAP: dict[str, tuple[str, ...]] = {
    # cli/main.py hosts the PR + duplicate-detection flows.
    "lib/vibe/cli/main.py": ("cli_main_pr", "duplicate_pr_prevention"),
    "lib/vibe/state.py": ("duplicate_pr_prevention",),
    # cli/ticket.py drives the --view/--unblocked surface tested in test_views.
    "lib/vibe/cli/ticket.py": ("cli_ticket", "views"),
    "lib/vibe/cli/costs.py": ("costs_cli",),
    # The Linear views feature is implemented in trackers/linear.py.
    "lib/vibe/trackers/linear.py": ("trackers_linear", "views"),
    "lib/vibe/trackers/shortcut.py": ("trackers_shortcut",),
    "lib/vibe/trackers/github_issues.py": ("trackers_github_issues",),
    "lib/vibe/trackers/": (
        "trackers_linear",
        "trackers_shortcut",
        "trackers_github_issues",
        "views",
    ),
    # wizards/<x>.py -> test_<x>_wizard / test_wizards_<x> (convention breaks).
    "lib/vibe/wizards/costs.py": ("costs_wizard",),
    "lib/vibe/wizards/github.py": ("wizards_github",),
    "lib/vibe/wizards/setup.py": ("setup",),
    "lib/vibe/wizards/": ("costs_wizard", "wizards_github", "setup"),
    # secrets/git/frontend packages each have a single differently-named suite.
    "lib/vibe/secrets/": ("secrets_providers",),
    "lib/vibe/git/": ("git_worktrees",),
    "lib/vibe/frontend/": ("frontend",),
}

# Integration / combinatorial seams: a real compose path between modules,
# tested under ``tests/integration/``. A change to ANY participant runs the
# seam's suite (in addition to the participants' own unit suites), because the
# bug a seam test catches lives in the *interaction*, which either side can
# break. Keys are integration test paths; values are participant source
# prefixes — an exact file, or a whole package when the key ends in "/".
#
# Add a seam ONLY where the modules are designed to compose in the product. Do
# not add one for every import edge — that re-couples the suite. ``test_testscope``
# asserts each suite file exists and each participant lives under ``lib/vibe/``.
INTEGRATION_SEAMS: dict[str, tuple[str, ...]] = {
    # create_worktree / cleanup_worktree drive the real state module to
    # register and deregister worktrees on disk.
    "tests/integration/test_worktree_state.py": (
        "lib/vibe/git/worktrees.py",
        "lib/vibe/state.py",
    ),
}


def _tests_for_source(path: str, known_stems: set[str]) -> set[str] | None:
    """Map one changed source path to test stems.

    Returns a (possibly empty) set of stems, or ``None`` to signal "run all"
    (an unmapped ``lib/vibe/`` change — fail safe).
    """
    # Explicit exact-file match wins.
    if path in SOURCE_TEST_MAP:
        return {s for s in SOURCE_TEST_MAP[path] if s in known_stems}

    # Explicit package-prefix match.
    for key, stems in SOURCE_TEST_MAP.items():
        if key.endswith("/") and path.startswith(key):
            return {s for s in stems if s in known_stems}

    if not path.startswith("lib/vibe/"):
        # Non-source change (docs, recipes, bin/, etc.) needs no pytest target.
        # bin/ wrappers are proven by the live smoke-test matrix, not pytest.
        return set()

    rest = path[len("lib/vibe/") :]
    parts = rest.split("/")

    if len(parts) == 1:
        # Top-level module: lib/vibe/<name>.py -> tests/test_<name>.py
        name = parts[0].removesuffix(".py")
        stem = name
        if stem in known_stems:
            return {stem}
        # No matching unit test for this module (e.g. cors.py, github_actions.py).
        # Nothing to scope to; main still runs the full suite as the backstop.
        return set()

    # Package: lib/vibe/<pkg>/... -> every test_<pkg>* suite.
    pkg = parts[0]
    matched = {s for s in known_stems if s == pkg or s.startswith(f"{pkg}_")}
    if matched:
        return matched
    # Known package with no convention-matching tests -> fail safe.
    return None


def discover_test_stems(tests_dir: Path) -> set[str]:
    """Return the set of available ``test_<stem>.py`` stems under *tests_dir*."""
    return {p.name[len("test_") : -len(".py")] for p in tests_dir.glob("test_*.py")}


def select_test_targets(
    changed_files: Iterable[str],
    known_stems: set[str],
) -> list[str] | str:
    """Decide which pytest targets to run for a set of changed files.

    Returns either :data:`RUN_ALL` (run the whole suite) or a sorted list of
    ``tests/test_*.py`` and ``tests/integration/test_*.py`` paths. An empty list
    means no Python tests are affected.
    """
    selected: set[str] = set()
    selected_paths: set[str] = set()

    for raw in changed_files:
        path = raw.strip()
        if not path:
            continue

        if any(path == p or path.startswith(p) for p in SHARED_PREFIXES):
            return RUN_ALL

        # Integration seams: a change to any participant runs the seam's suite.
        for seam_path, participants in INTEGRATION_SEAMS.items():
            if any(
                path == part or (part.endswith("/") and path.startswith(part))
                for part in participants
            ):
                selected_paths.add(seam_path)

        # A changed integration test always runs itself.
        if path.startswith("tests/integration/test_") and path.endswith(".py"):
            selected_paths.add(path)
            continue

        # A changed unit test file always runs itself.
        if path.startswith("tests/test_") and path.endswith(".py"):
            stem = path[len("tests/test_") : -len(".py")]
            if stem in known_stems:
                selected.add(stem)
            continue

        result = _tests_for_source(path, known_stems)
        if result is None:
            return RUN_ALL
        selected.update(result)

    unit_paths = {f"tests/test_{stem}.py" for stem in selected}
    return sorted(unit_paths | selected_paths)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint: read changed paths, print pytest targets (or ``ALL``).

    Changed paths come from positional args, or from stdin (one per line) when
    no args are given. Prints ``ALL`` to run the full suite, an empty line when
    no Python tests are affected, or space-separated ``tests/test_*.py`` paths.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"-h", "--help"}:
        print(main.__doc__)
        return 0

    if args:
        changed = args
    else:
        changed = sys.stdin.read().splitlines()

    tests_dir = Path(__file__).resolve().parent.parent.parent / "tests"
    known = discover_test_stems(tests_dir) if tests_dir.is_dir() else set()

    targets = select_test_targets(changed, known)
    if targets == RUN_ALL:
        print(RUN_ALL)
    else:
        print(" ".join(targets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
