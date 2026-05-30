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

1. **One module = one test file.** `lib/vibe/<name>.py` is covered by
   `tests/test_<name>.py`; a package `lib/vibe/<pkg>/` is covered by
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

`lib/vibe/testscope.py` decides which pytest targets a change needs, and
`.github/workflows/tests.yml` uses it:

| Trigger | What runs |
|---------|-----------|
| Push to `main` | **Full suite** (the safety net before release) |
| Change to a shared/core file — exactly the `SHARED_PREFIXES` list in `testscope.py`: `pyproject.toml`, `tests/conftest.py`, `tests/__init__.py`, `lib/vibe/__init__.py`, `config.py`, `config_schema.py`, `env.py`, `utils/`, the selector (`testscope.py`), the workflow | **Full suite** (blast radius is everything) |
| PR touching one mapped module | **Only that module's** `tests/test_*.py` |
| Unmapped `lib/vibe/` **package** (`lib/vibe/<pkg>/…` with no convention-matching tests) | **Full suite** (fail-safe — a forgotten mapping costs time, never coverage) |
| Unmapped top-level `lib/vibe/<name>.py` with no `tests/test_<name>.py` | **No pytest** (nothing to scope to; `main` is the backstop) |
| Docs / recipes / `bin/` only | **No pytest** (`bin/` wrappers are proven by the live smoke-test matrix) |

The tradeoff is deliberate: PR runs are scoped for fast feedback; a cross-module
dependency a scoped run misses is caught by the full suite on `main` before
anything ships. **Local stays the source of truth** — `bin/ci-local` runs the
full suite; CI scoping is the fast safety net, not the primary verification.

### Keeping the map honest

When you add a module or a test file, update `SOURCE_TEST_MAP` in
`lib/vibe/testscope.py` only if the naming convention doesn't already connect
them (most don't need an entry). `tests/test_testscope.py` fails if the map ever
references a test file that doesn't exist.

Try it locally:

```bash
# What would CI run for these changes?
PYTHONPATH=. python -m lib.vibe.testscope lib/vibe/trackers/linear.py
#   -> tests/test_trackers_linear.py tests/test_views.py

git diff --name-only origin/main...HEAD | PYTHONPATH=. python -m lib.vibe.testscope
#   -> ALL | <space-separated paths> | <empty: no Python tests affected>
```
