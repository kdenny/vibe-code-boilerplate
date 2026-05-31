# Modular Testing

How testing works during (and after) the VIBE revamp. This codifies the
**"Tests at the right level"** target in [`CLAUDE.md`](../../CLAUDE.md) into a
concrete policy and the CI that enforces it. The goal: tests that match the
module structure, run fast on every PR, and don't break for the wrong reasons
when a module is rewritten.

## The principle

> Module-level unit tests per module, plus combinatorial / integration suites
> **only** where modules are designed to compose. Don't add integration tests
> for modules that aren't meant to interact.
> — `CLAUDE.md`, *Target shape*

## Five rules

1. **One module = one test file.** `vibe/<name>.py` is covered by
   `tests/test_<name>.py`; a package `vibe/<pkg>/` is covered by
   `tests/test_<pkg>_*.py`. Keep the mapping obvious — it's what makes
   module-scoped CI possible.
2. **Test public behavior, not internals.** Exercise the functions other
   modules call. A test that pins a private helper (`_parse_issue`,
   `_get_label_ids`) breaks on harmless refactors for no safety gain. If a
   private function is complex enough to need direct tests, that's a signal it
   should be public or extracted.
3. **Mock at the boundary, not the middle.** Mock the network, the clock, the
   filesystem edge — not the module's own collaborators. A test that mocks so
   much it only asserts "the mock was called" exercises nothing. CodeRabbit is
   configured to flag these (`.coderabbit.yaml`, `tests/**`).
4. **Parametrize instead of copy-paste.** Three near-identical cases that vary
   only in input/expected output are one `@pytest.mark.parametrize`, not three
   functions. Same coverage, a third of the lines, one place to change.
5. **Integration tests only at real seams.** Write a cross-module / combinatorial
   test only where two modules are *designed* to compose (e.g. CLI → tracker).
   Don't synthesize interactions that don't exist in the product.

## Two test levels

The suite has two levels, and the layout makes the level obvious:

| Level | Lives in | Covers | Mocks |
|-------|----------|--------|-------|
| **Unit** | `tests/test_<module>.py` | one module in isolation | the network/clock/fs **boundary** only |
| **Integration** | `tests/integration/test_<seam>.py` | a real compose **seam** between modules | only the true I/O boundary — *never the collaborating module* |

The distinction matters because of rule 3: a unit test that mocks its
collaborator (e.g. `tests/test_git_worktrees.py` mocks out `state.add_worktree`)
proves the module calls *something*, but never proves the two modules actually
compose. That's what an integration suite is for — it runs the real
collaborator and asserts the observable result of the interaction.

> **Worked example.** `tests/integration/test_worktree_state.py` exercises the
> `git.worktrees` ↔ `state` seam: it mocks only the git subprocess and lets
> `create_worktree` drive the *real* `state` module, then asserts the worktree
> was persisted to `.vibe/local_state.json` on disk. No mock of the collaborator.

**Add an integration suite only at a seam the product actually has.** A "seam"
needs ≥2 modules designed to compose (`test_testscope.py` enforces this). Don't
add one for every import edge — that re-couples the suite you're trying to keep
modular.

## When you rewrite a module

The revamp rewrites modules in place, non-destructively. When you rewrite a
module, **re-level its tests in the same PR**:

- Keep the public-behavior tests as the rewrite's *contract* — they should pass
  before and after.
- Delete tests that only pinned the old internals.
- Collapse duplicated cases into parametrized ones.
- Don't pre-emptively gut a module's tests in a separate PR ahead of its
  rewrite — that's churn without a safety story, and it splits the contract
  from the code it guards.

## Module-scoped CI

`vibe/testscope.py` decides which pytest targets a change needs, and
`.github/workflows/tests.yml` uses it:

| Trigger | What runs |
|---------|-----------|
| Push to `main` | **Full suite** (the safety net before release) |
| Change to a shared/core file — exactly the `SHARED_PREFIXES` list in `testscope.py`: `pyproject.toml`, `tests/conftest.py`, `tests/__init__.py`, `vibe/__init__.py`, `vibe/config.py`, `vibe/config_schema.py`, `vibe/env.py`, `vibe/utils/`, the selector (`vibe/testscope.py`), the workflow | **Full suite** (blast radius is everything) |
| PR touching one mapped module | **Only that module's** `tests/test_*.py` |
| PR touching either side of a compose seam | that module's unit suite **plus** the seam's `tests/integration/test_*.py` |
| Unmapped `vibe/` **package** (`vibe/<pkg>/…` with no convention-matching tests) | **Full suite** (fail-safe — a forgotten mapping costs time, never coverage) |
| Unmapped top-level `vibe/<name>.py` with no `tests/test_<name>.py` | **No pytest** (nothing to scope to; `main` is the backstop) |
| Docs / recipes / `bin/` only | **No pytest** (`bin/` wrappers are proven by the live smoke-test matrix) |

The tradeoff is deliberate: PR runs are scoped for fast feedback; a cross-module
dependency a scoped run misses is caught by the full suite on `main` before
anything ships. **Local stays the source of truth** — `bin/ci-local` runs the
full suite; CI scoping is the fast safety net, not the primary verification.

### Keeping the map honest

When you add a module or a test file, update `SOURCE_TEST_MAP` in
`vibe/testscope.py` only if the naming convention doesn't already connect
them (most don't need an entry). When you add an **integration suite**, add an
entry to `INTEGRATION_SEAMS` listing its participant source paths.
`tests/test_testscope.py` fails if either map references a test file that
doesn't exist, if a seam participant isn't under `vibe/`, or if a seam has
fewer than two participants.

Try it locally:

```bash
# What would CI run for these changes?
PYTHONPATH=. python -m vibe.testscope vibe/trackers/linear.py
#   -> tests/test_trackers_linear.py tests/test_views.py

git diff --name-only origin/main...HEAD | PYTHONPATH=. python -m vibe.testscope
#   -> ALL | <space-separated paths> | <empty: no Python tests affected>
```

### The one command the runner (and you) call: `bin/ci-local --scope`

`testscope.py` is the selector; `bin/ci-local --scope` is the **single command**
that turns its verdict into an actual scoped run. It is what a cloud agent's QA
path invokes, and what you run locally to feel the same thing (VIBE-186).

```bash
bin/ci-local --scope                      # auto-diff this branch vs origin/main
bin/ci-local --scope vibe/trackers/linear.py   # explicit changed-file list
```

It maps the changed set → suites via `testscope.py` (no duplicated selection
logic anywhere — the GitHub workflow and this command both shell out to the same
module), then:

| `testscope.py` verdict | `--scope` behaviour |
|------------------------|---------------------|
| a list of suites | runs **only** those (`pytest (scoped)`) |
| `ALL` | runs the **full** suite (`pytest (full — shared change)`) |
| empty | **skips** pytest (no changed file maps to a suite) |

Lint and secret scans always run on the whole tree (they're fast); only pytest —
the dominant cost — is scoped. With no `--scope`, `bin/ci-local` runs the full
suite: **local is the source of truth**, `--scope` is the fast warm-loop path.

### When full-tree validation is still required

`--scope` is for fast feedback on a focused change. The full suite still runs —
automatically — in these cases, and you should reach for an unscoped
`bin/ci-local` whenever you're unsure:

- **Push to `main`** — the release backstop always runs everything (workflow).
- **A shared/contract file changed** — exactly the `SHARED_PREFIXES` list
  (`pyproject.toml`, the lockfile closures via it, `vibe/config.py`,
  `vibe/config_schema.py`, `vibe/env.py`, `vibe/utils/`, `vibe/testscope.py`, the workflow). Their
  blast radius is the whole package, so `testscope.py` returns `ALL` and
  `--scope` expands to the full run on its own.
- **A new/unmapped `vibe/` package** — fail-safe: `testscope.py` returns
  `ALL` rather than risk skipping an untested change.
- **A cross-cutting refactor** that touches many modules — `--scope` will run
  every affected suite, but when the change is broad enough that the *interaction*
  matters, prefer the full `bin/ci-local`.

The tradeoff is deliberate and unchanged: scoped runs trade exhaustiveness for
speed on PRs; the full suite on `main` is the safety net before release. See
[`recipes/environments/cloud-bootstrap.md`](../environments/cloud-bootstrap.md)
for how this composes with the cached install into the cold/warm budget.
