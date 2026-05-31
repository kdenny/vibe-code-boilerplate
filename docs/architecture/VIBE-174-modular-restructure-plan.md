# VIBE-174 — Modular, Local-First Restructure: Research & Implementation Plan

**Ticket:** [VIBE-174 — Restructure VIBE repo for modular local-first agent execution](https://linear.app/2wrist/issue/VIBE-174/restructure-vibe-repo-for-modular-local-first-agent-execution)
**Status:** Living plan. Agent-ready. Built on the VIBE-137 baseline (cruft removed + module-scoped CI rail).
**Deliverable type:** Research + agent-ready implementation plan, **plus** the first staged execution step (the integration-test seam layer) landed in the same PR.

> **SYNC NOTE — this doc and Linear are a matched pair.** The canonical copy of
> this plan lives here in the repo; a condensed summary lives on the VIBE-174
> Linear ticket. **If one moves, move the other in the same change.** When the
> repo structure, the validation contract, or the staged sequence below changes,
> update this file *and* the Linear ticket body, and note it in the PR. This
> mirrors the CLAUDE.md ↔ `.coderabbit.yaml` sync rule.

---

## 0. TL;DR

The repo is **already a clean, acyclic, modular package** — the restructure is
about *formalizing and enforcing* the seams that already exist, not relocating
files. The fastest path to "reliable one-shot agent work" is:

1. A **module contract** every package can be held to (explicit public surface,
   declared dependencies, one unit suite, declared compose seams).
2. A **two-level test strategy** — isolated unit tests + combinatorial
   integration tests *only at real seams* — both wired into the module-scoped CI
   that VIBE-137 introduced.
3. A **minimal, fast, local-first validation contract** (`bin/ci-local`) that an
   agent can rely on as the single source of truth.

**What this PR executes (staged step 1 of the sequence in §6):** the integration
-test seam layer — `tests/integration/`, `INTEGRATION_SEAMS` in
`vibe/testscope.py`, the first real seam suite (`git.worktrees ↔ state`), and
the policy update in `recipes/testing/modular-testing.md`. Everything else is
sequenced below as agent-ready follow-ups. This mirrors VIBE-137's "build the
rail + demonstrate once" pattern instead of a big-bang rewrite.

---

## 1. Where we are (research findings)

### 1.1 Current shape

```
bin/                 # thin CLI wrappers: vibe, ticket, costs, secrets, doctor, logs, ci-local
vibe/            # the package
  cli/               # click entrypoints (main, ticket, costs, secrets, figma)
  trackers/          # Linear / Shortcut / GitHub-issues (+ base)
  costs/             # cost model + providers/* (8, dynamically loaded)
  secrets/           # allowlist + providers/* (3, dynamically loaded)
  integrations/      # publishable integration registry consumers (VIBE-86 seam)
  wizards/           # setup + per-integration wizards
  git/               # branches, worktrees
  ui/                # reusable terminal UI components
  agents/, frontend/, retrofit/   # feature packages
  utils/             # cache, debug, file_lock, retry
  config.py, config_schema.py, env.py, state.py, tools.py, ...  # top-level modules
  testscope.py       # module-scoped CI selector (added by VIBE-137)
tests/               # one suite per module: test_<module>.py / test_<pkg>_*.py
  integration/       # NEW (this PR): combinatorial suites at real seams
recipes/             # how-to docs (incl. testing/modular-testing.md — the policy)
docs/                # architecture, decisions (ADRs), review, cleanup, archive
agent_instructions/  # CORE/CLI/COMMANDS/WORKFLOW (regeneration paused during revamp)
```

### 1.2 Dependency graph — acyclic, with a clear core

A full internal-import sweep found **no cycles**. The hub analysis:

| Tier | Modules | Evidence |
|------|---------|----------|
| **Core / shared** (high fan-in, imported across the package) | `config`, `config_schema`, `env`, `state`, `utils/` | already in `testscope.SHARED_PREFIXES` → a change runs the full suite |
| **Un-tracked hubs** (high fan-in, *not* yet treated as shared) | `ui/` (≈6 importers), `tools.py` (≈12 wizard importers) | **finding F1** below |
| **Orchestrators** (high fan-out) | `cli/main.py` (~20 deps), `wizards/setup.py` (~12), `doctor.py` | these are the natural seam owners |
| **Pluggable leaves** | `costs/providers/*`, `secrets/providers/*`, `trackers/*` | dynamically loaded; already plugin-shaped |

**Implication:** the modular target is *within reach* — the boundaries are real
and mostly clean. The work is to make them **explicit and enforced**, and to
stop the few reach-throughs from rotting into hidden coupling.

### 1.3 Public-API discipline (per `__init__.py`)

Most packages export an explicit `__all__` (`agents`, `costs`, `git`, `retrofit`,
`secrets`, `trackers`, `ui`, `frontend`). Gaps found:

- **`trackers/__init__.py` omits `ShortcutTracker`** from `__all__` (exports
  `TrackerBase`, `GitHubIssuesTracker`, `LinearTracker` only). Inconsistent
  public surface → **finding F2**.
- **`cli/__init__.py` is empty** (passthrough). Acceptable for an entrypoint
  package but means there is no declared CLI surface → **finding F3**.
- **`wizards/__init__.py` exports only `run_setup`**, forcing callers
  (`cli/main.py`, `doctor.py`) to reach into `wizards.<x>` directly → **finding F4**.

### 1.4 Reach-throughs (where coupling could rot)

No private (`_`-prefixed) cross-module imports were found — good. The deep
imports that exist are all at **orchestration points** and are the *real compose
seams* (§4). The ones to watch (candidates for going through a package surface
instead): `cli/secrets.py` → `secrets.providers.*` (dynamic), `wizards/setup.py`
→ `wizards.*`, `doctor.py` → `wizards.github` / `secrets.allowlist` / `ui.validation`.

### 1.5 Seam asymmetry found while writing the first integration test (F5)

`git.worktrees.create_worktree` records state under the **primary repo root**
(`add_worktree(..., base_path=repo_root)`), but `cleanup_worktree` calls
`remove_worktree(worktree_path)` **without** a `base_path`, so it reads/writes a
**CWD-relative** `.vibe/local_state.json`. When an agent runs cleanup from a
directory other than the primary repo root, the create and cleanup touch
*different state files*. This is exactly the class of bug the integration layer
exists to catch. Behavior-preserving fix tracked as a follow-up (§8).

---

## 2. Target repo structure (modular development + testing)

The target is **not** a new directory tree — it's a **contract** every module is
held to, plus the existing layout made explicit.

### 2.1 The module contract

Every `vibe/<module>` (a package *or* a top-level `.py`) must satisfy:

1. **Explicit public surface.** A package declares `__all__` in its `__init__.py`;
   that list *is* the module's API. Callers import from the package
   (`from vibe.trackers import LinearTracker`), never a deep submodule.
2. **Declared dependencies.** A module imports only the core tier and the public
   surfaces of its declared collaborators — no reach-through into another
   package's internals, no new global state.
3. **One unit suite.** `vibe/<name>.py → tests/test_<name>.py`;
   `vibe/<pkg>/ → tests/test_<pkg>_*.py`. (Already enforced by `testscope`.)
4. **Runs and tests in isolation.** The module can be imported and its unit suite
   run without standing up the whole app.
5. **Declared compose seams.** Where a module is *designed* to compose with
   another, that seam has an integration suite registered in `INTEGRATION_SEAMS`.

### 2.2 Two test levels, made structural

- **Unit:** `tests/test_<module>.py` — one module, collaborators mocked at the
  I/O boundary.
- **Integration:** `tests/integration/test_<seam>.py` — a real seam, only the
  true boundary mocked, **never** the collaborating module.

This is the dimension VIBE-137 didn't build and **this PR adds** (§5).

### 2.3 Packaging boundary (toward DEAL)

The downstream goal (§7) is to ship the **PR-autopilot capability** as a
package. The module contract is what makes that extractable: a package with an
explicit surface, declared deps, and its own suites can be lifted into a
distributable without dragging the whole repo. Provider packages
(`costs/providers`, `secrets/providers`, `trackers`) are already plugin-shaped
and are the cleanest first extraction candidates — but extraction itself is
owned by the **VIBE-86 line**, not this ticket (we don't duplicate it).

---

## 3. Fast, local-first setup + the validation contract

**Principle (CLAUDE.md speed rule):** local is the source of truth; CI is the
fast safety net. An agent must be able to trust one command.

### 3.1 The validation contract an agent can rely on

| Command | Guarantee | Speed lever |
|---------|-----------|-------------|
| `bin/ci-local` | Runs every locally-runnable check (ruff check + format, mypy on `vibe/`, full pytest, gitleaks, project hooks). Exit 0 **with no `⚠ … SKIPPED` warning** ⇒ safe to push. Resolves ruff/mypy/pytest from the project venv (`.venv`/`.direnv`) even when it's off `PATH`. | `--fast` skips frontend tests; non-core tools **skip** (yellow `–`); a missing **core linter** (ruff/mypy) warns **loudly** (`⚠ … SKIPPED`, "not a clean pass") — never silent, never fatal, but a warned run is **not** a clean pass |
| `bin/ci-local --fast` | Same, minus slow frontend tests | for tight inner loops |
| `PYTHONPATH=. python -m vibe.testscope <paths>` | Prints exactly which suites CI will run for a change (`ALL` / paths / empty) | lets an agent predict CI scope before pushing |
| `bin/<cli> --help` + per-subcommand live smoke test | CLI behavior proof (CLI doctrine) | live runs only; documented matrix in the PR |

**Minimal bootstrap:** Python ≥3.11, `pip install -e ".[dev]"` (pytest, mypy,
ruff). Everything else (gitleaks, npm, mypy) degrades to a SKIP. No service
account or network needed to validate a change locally.

### 3.2 Module-scoped CI (the speed rail, from VIBE-137)

`vibe/testscope.py` maps a diff → the minimal set of suites. PRs run only
affected modules; `main` and shared-file changes run the full suite. **This PR
extends it to integration seams** (§5) without changing that contract.

### 3.3 Speed opportunities surfaced (CLAUDE.md speed rule)

- **S1 — `bin/` venv bootstrap duplication** is being removed via `.direnv`
  (VIBE-176). Once it lands, the per-script ~20-line venv plumbing goes away;
  re-validate `bin/ci-local` startup time after.
- **S2 — `ui/` and `tools.py` are hubs but not in `SHARED_PREFIXES`** (F1). They
  are *under*-scoped (a public-API change there can break importers a scoped PR
  run won't exercise). Promoting them to shared trades a little speed for
  correctness — see §8 for the precise call.
- **S3 — integration suites must stay cheap.** They mock only the boundary; if a
  seam suite needs real network/services it doesn't belong in `tests/integration/`.

---

## 4. How modules integrate (explicit interfaces, not hidden coupling)

Integration happens at **named seams**, each owned by an orchestrator. The real
seams in the product today (where combinatorial tests belong):

| Seam | Owner | What composes |
|------|-------|---------------|
| `cli.main ↔ trackers` | `cli/main.py` | `vibe do TICKET` selects a tracker, fetches the ticket |
| `cli.ticket ↔ trackers` | `cli/ticket.py` | `ticket list/get/--view` per backend |
| `cli.main ↔ git` | `cli/main.py` | branch/worktree creation on `vibe do` |
| **`git.worktrees ↔ state`** | `git/worktrees.py` | **register/deregister worktrees on disk — covered this PR** |
| `cli.secrets ↔ secrets.providers` | `cli/secrets.py` | `secrets sync` to Vercel/Fly/GitHub |
| `cli.costs ↔ costs.registry` | `cli/costs.py` | `costs` aggregates providers |
| `wizards.setup ↔ {trackers, secrets, ui, agents}` | `wizards/setup.py` | full `vibe setup` flow writes config |
| `retrofit.applier ↔ config` | `retrofit/applier.py` | retrofit preserves manual config |
| `update_check ↔ version` | `update_check.py` | update notice on startup |

**Rule:** a seam earns an integration suite only when the two modules are
*designed* to compose in the product. Don't synthesize interactions (e.g. don't
write a `frontend ↔ trackers` test — they never touch).

---

## 5. Testing strategy (and the rail this PR adds)

### 5.1 Unit level — unchanged

Per `recipes/testing/modular-testing.md`: one module = one suite; test public
behavior not internals; mock at the boundary; parametrize; re-level a module's
tests in the same PR as its rewrite.

### 5.2 Integration level — **added in this PR**

- **Layout:** `tests/integration/test_<seam>.py`.
- **Selector:** `INTEGRATION_SEAMS` in `testscope.py` maps each suite to its
  participant source paths. A change to **any** participant runs the suite, on
  top of the participants' unit suites. Fail-safe and `main`-runs-all semantics
  are preserved.
- **Integrity guards** (`tests/test_testscope.py`): every seam suite file must
  exist; every participant must live under `vibe/`; a seam needs ≥2
  participants (a 1-participant "seam" is just a unit test).
- **First suite:** `tests/integration/test_worktree_state.py` exercises
  `git.worktrees ↔ state` with the real `state` module and only the git
  subprocess mocked — directly closing the gap that
  `tests/test_git_worktrees.py` mocks `add_worktree` away.

### 5.3 Backlog of seams to cover (sequenced in §6)

The §4 table is the backlog. Add suites incrementally, highest-risk first:
`wizards.setup ↔ *` (most fan-out, least covered) and `cli ↔ trackers` (the core
agent loop) are the next two.

---

## 6. Staged migration plan (agent-ready)

Each step is a separate PR, behavior-preserving, green on `bin/ci-local`, sized
to *not* be a big-bang. Steps are independent unless noted.

| # | Step | Scope | Acceptance | Status |
|---|------|-------|-----------|--------|
| **1** | **Integration-seam test layer** | `tests/integration/`, `INTEGRATION_SEAMS`, first seam suite, recipe + CLAUDE.md/`.coderabbit.yaml` | seam suite runs on either side's change; integrity tests pass; `ci-local` green | **✅ this PR** |
| 2 | **Codify the module contract** | A short `docs/architecture/module-contract.md` + a lightweight check (test) that every `vibe/<pkg>/__init__.py` declares `__all__` | check passes for all packages; documented exceptions (`cli`, `utils`) listed | ⏭️ next |
| 3 | **Close public-API gaps** (F2–F4) | export `ShortcutTracker`; decide `wizards`/`cli` surfaces | `from vibe.trackers import ShortcutTracker` works; importers updated; tests at boundary | ⏭️ |
| 4 | **Hub scoping decision** (F1/S2) | add `ui/` and/or `tools.py` to `SHARED_PREFIXES` *or* document why not | `testscope` change + `test_testscope` update | ⏭️ |
| 5 | **Cover the next seams** | add `wizards.setup ↔ *` and `cli ↔ trackers` integration suites | each seam runs real collaborators, boundary-only mocks | ⏭️ |
| 6 | **Fix the worktree/state base_path asymmetry** (F5) | thread `base_path` through `cleanup_worktree` | a cleanup-from-elsewhere integration test passes | ⏭️ |
| 7 | **Per-module test re-leveling** | apply the thinning targets from the VIBE-137 audit *as each module is rewritten* | per `modular-testing.md`; no separate gutting PR | ⏭️ ongoing |
| 8 | **Integration registration seam** | `vibe/cli/registry.py`, `vibe/integrations/`, packaging docs, guardrail tests | integration declares config/verbs/entrypoints/extra; missing extra is actionable; app-code imports fail guardrail | ✅ VIBE-86; VIBE-179 extends this with pre-engine configure/status verbs |
| 9 | **Package namespace scaffold** | move the import package from `lib/vibe` to top-level `vibe`, add `vibe.__main__`, and wire packaging/CI selectors to the new path | `import vibe`, `python -m vibe`, and the `vibe` console entry work; no code imports `lib.vibe`; module scoping still selects the right suites | ✅ VIBE-182 |
| — | **Module extraction → package** | provider packages first; PR Autopilot engine lands behind the VIBE-86 seam | owned by **VIBE-128/VIBE-85 follow-ups**, not this structural plan | 🔗 |

> **Non-destructive discipline:** no step relocates working code without a test
> proving behavior is preserved. Steps 2–6 are each small enough to review in
> one sitting. If a step grows, split it.

---

## 7. Critical path to packaged PR Autopilot in DEAL

The downstream goal is to ship VIBE's **PR-autopilot capability** (agent-PR
contract + review firewall + module-scoped validation) as something DEAL can
install. The structure choices above are chosen to move toward that:

1. **Module contract (steps 2–4)** → packages have explicit surfaces and declared
   deps, so the autopilot-relevant modules can be lifted without the whole repo.
2. **Two-level testing (steps 1, 5)** → the extracted package ships with suites
   that run in isolation *and* prove its seams, so DEAL can trust it.
3. **Validation contract (§3)** → `bin/ci-local` + module-scoped CI is the
   reusable "does this change pass?" gate the autopilot leans on.
4. **VIBE-86 integration seam + VIBE-179 configuration DX + VIBE-146 telemetry**
   → the live registry, reference `pr_autopilot` skeleton, extra-gated engine
   dispatch, pre-engine configure/status/inspect/enable/disable verbs, layered
   `.vibe/` TOML artifacts, Linear-visible run telemetry, and app-code import
   guardrail give VIBE-128 a package boundary, operator-facing desired-state
   contract, and failure-observability contract to plug into.

The packaging spec and milestone live in VIBE-83/88 and the
[packaged-vibe publish milestone](https://linear.app/2wrist/issue/VIBE-83). This
plan is the *structural enabler*; it does not itself publish the package.

---

## 8. Findings & follow-up tickets

| ID | Finding | Recommendation | Where |
|----|---------|----------------|-------|
| F1 | `ui/` and `tools.py` are hubs not in `SHARED_PREFIXES` | Step 4: promote to shared, or document the accepted under-scoping | `testscope.py` |
| F2 | `trackers/__init__.py` omits `ShortcutTracker` | Step 3 | `vibe/trackers/__init__.py` |
| F3 | `cli/__init__.py` empty (no declared surface) | Step 2/3: decide if CLI needs a surface | `vibe/cli/__init__.py` |
| F4 | `wizards/__init__.py` exports only `run_setup` | Step 3: export the feature wizards or accept reach-through | `vibe/wizards/__init__.py` |
| F5 | `create_worktree` (repo-root state) vs `cleanup_worktree` (CWD-relative state) base_path asymmetry | Step 6: thread `base_path`; add a cleanup integration test | `vibe/git/worktrees.py` |

> Each becomes a Linear follow-up with a Low/Medium risk label when scheduled.
> F5 should be filed Medium (latent state-corruption when cwd ≠ repo root).

---

## 9. Risks & non-goals

- **Non-goal: unplanned code relocation.** VIBE-182 performed the planned
  namespace move to `vibe/`; future relocation churn without a
  behavior-preserving proof is explicitly out of scope.
- **Non-goal: PR Autopilot engine extraction.** VIBE-86 provides the seam; the
  actual engine remains owned by VIBE-128 and release packaging by VIBE-85.
- **Risk: testscope churn vs VIBE-137.** This PR is branched off VIBE-137 (in
  review). The `testscope.py` edits are additive (new `INTEGRATION_SEAMS` + new
  branches in `select_test_targets`) to minimize rebase conflict if 137 changes.
- **Risk: integration suites drifting into slow/flaky service tests.** Guarded by
  policy (boundary-only mocks) and the ≥2-participant integrity check.
