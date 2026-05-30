# CLAUDE.md — VIBE Repo (Target-State Contract, Revamp Period)

> **Status: TARGET-STATE CONTRACT.** This repo is being restructured into a
> modular, local-first toolkit on the critical path to packaging **PR Autopilot**
> for **DEAL**. This file describes the **architecture we are building toward**
> and is the live contract between agents and reviewers during the revamp.
>
> **Built vs Target.** Most of the structure below already exists (the package is
> modular and acyclic; module-scoped CI and the two-level test strategy are live).
> Items not yet fully in place are marked **🎯 Target** — treat them as the
> direction every PR should move toward, never away from. The detailed,
> agent-ready sequencing lives in
> [`docs/architecture/VIBE-174-modular-restructure-plan.md`](docs/architecture/VIBE-174-modular-restructure-plan.md).
>
> The pre-revamp boilerplate instructions are archived verbatim at
> [`docs/archive/CLAUDE.boilerplate.md`](docs/archive/CLAUDE.boilerplate.md) —
> the full operational detail on tickets, worktrees, labels, deployment wizards,
> and recipes. Nothing was deleted; it was moved. This file is **hand-authored
> for the revamp**; do not regenerate it from `agent_instructions/` until the
> revamp completes and this notice is removed.

---

## Three standing rules (read these first)

1. **Sync rule — the contract tracks the architecture.** Any substantial change
   to repo structure, module boundaries, the local run/validation flow, the
   testing strategy, or the agent-PR contract MUST update
   [`.coderabbit.yaml`](.coderabbit.yaml) **and** the plan doc
   ([`docs/architecture/VIBE-174-modular-restructure-plan.md`](docs/architecture/VIBE-174-modular-restructure-plan.md))
   **in the same PR**. CLAUDE.md, `.coderabbit.yaml`, and the plan are a matched
   set; the plan also has a paired Linear summary. **[`AGENTS.md`](AGENTS.md) is
   the agent-facing operational mirror of this contract** (what a Cursor/cloud
   agent reads from the checkout) — CLAUDE.md stays canonical, but a change to the
   PR policy, the run/validation flow, or the agent-PR contract must keep
   `AGENTS.md` consistent in the same PR. A PR that shifts the architecture
   without syncing these is incomplete, and CodeRabbit is configured to request
   changes on it.

2. **Speed rule — always surface ways to go faster.** This project is optimized
   for speed: fast local setup, fast local validation, tight agent loops. If you
   (agent or reviewer) ever see a way to make setup faster, validation faster, or
   the loop tighter, **surface it** — in the PR description, in a review comment,
   or as a follow-up ticket — even when the change in front of you is otherwise
   fine. Don't sit on a speed idea.

3. **Scoping rule — `agent-ready` is a promise; honor the rubric.** The board is
   an agent execution queue, so a label must mean exactly one thing. Before you
   apply `agent-ready` / `needs-scoping` / `wall` / `gate` to a ticket — or pull
   one to work on — check it against
   [`docs/review/agent-ready-rubric.md`](docs/review/agent-ready-rubric.md).
   `agent-ready` means *no open design decision is left to the agent* (it may
   still be blocked); a hidden dependency on a not-yet-built contract is the most
   common way a ticket is falsely `agent-ready` — wire the `blocked-by` edge or
   demote to `needs-scoping` with the open questions written out.

---

## What this repo is

VIBE is a language-agnostic workflow-automation toolkit (Python `bin/*` CLIs +
the `lib/vibe/` package) that runs *alongside* a project to manage tickets,
worktrees, PR policy, and integrations. The current effort is a **non-destructive
revamp**: formalize and enforce the module seams that already exist — explicit
public surfaces, declared dependencies, isolated + seam-level tests — on the
critical path toward packaging the **PR Autopilot** capability for downstream
adoption in **DEAL**.

The repo is already a clean, acyclic, modular package. The revamp is about making
its boundaries **explicit and enforced**, not relocating files.

---

## Target shape (the module contract)

Every `lib/vibe/<module>` — a package or a top-level `.py` — is held to a
**module contract**:

1. **Explicit public surface.** A package declares `__all__` in its `__init__.py`;
   that list *is* its API. Import from the package
   (`from lib.vibe.trackers import LinearTracker`), never a deep submodule. 🎯
   *Target: a check enforces `__all__` on every package — see plan step 2.*
2. **Declared dependencies.** Import only the core tier (`config`, `config_schema`,
   `env`, `state`, `utils/`) and the **public surfaces** of declared
   collaborators. No reach-through into another package's internals; no new
   global state.
3. **One unit suite.** `lib/vibe/<name>.py → tests/test_<name>.py`;
   `lib/vibe/<pkg>/ → tests/test_<pkg>_*.py`. Enforced by `lib/vibe/testscope.py`.
4. **Runs and tests in isolation.** A module imports and its unit suite runs
   without standing up the whole app.
5. **Declared compose seams.** Where a module is *designed* to compose with
   another, that seam has an integration suite registered in `INTEGRATION_SEAMS`
   (`lib/vibe/testscope.py`).

The toolkit stays **fast to set up and validate**: minimal bootstrap, `bin/ci-local`
as the one-command local check, module-scoped CI as the fast safety net.

---

## Migration posture: non-destructive, staged

- **Preserve behavior.** Working commands keep working. Refactors are
  behavior-preserving unless the ticket explicitly says otherwise.
- **Stage, don't big-bang.** Prefer incremental extraction (one seam at a time,
  kept green) over sweeping rewrites. A PR that churns large surface area without
  a staged justification should be split. (The plan doc sequences the steps.)
- **Keep modules independently runnable and testable.** A module you touch must
  still run and be tested in isolation, not only inside the full app.
- **Integrate through explicit interfaces.** Compose modules via public surfaces,
  not hidden coupling, shared globals, or reach-through into internals.
- **Prove local validation stays fast and reliable.** New structure and tests
  must show that local run + validation remain quick and trustworthy.

---

## Testing strategy (two levels)

Full policy: [`recipes/testing/modular-testing.md`](recipes/testing/modular-testing.md).

- **Unit** — `tests/test_<module>.py`. One module in isolation; test public
  behavior not internals; mock at the I/O **boundary**; parametrize near-identical
  cases.
- **Integration** — `tests/integration/test_<seam>.py`. A real compose **seam**
  between modules; run the real collaborators, mock **only** the true boundary
  (network/subprocess/fs). Add a seam **only** where modules are designed to
  compose in the product (≥2 participants); never synthesize interactions.

**Module-scoped CI** (`lib/vibe/testscope.py` + `.github/workflows/tests.yml`):

| Trigger | What runs |
|---------|-----------|
| Push to `main` | **Full suite** (the safety net before release) |
| Shared/core file changed (`SHARED_PREFIXES`: `config`, `config_schema`, `env`, `utils/`, `conftest`, `pyproject`, the selector, the workflow) | **Full suite** (blast radius is everything) |
| PR touching one module | **Only that module's** `tests/test_*.py` |
| PR touching either side of a compose seam | the unit suite **plus** the seam's `tests/integration/test_*.py` |
| Unmapped `lib/vibe/` path | **Full suite** (fail safe — a forgotten mapping costs time, never coverage) |
| Docs / recipes / `bin/` only | **No pytest** (`bin/` wrappers are proven by the live smoke-test matrix) |

**Local is the source of truth.** `bin/ci-local` runs the full suite; CI scoping
is the fast safety net, not the primary verification. Predict CI scope with
`PYTHONPATH=. python -m lib.vibe.testscope <changed paths>`, or run the scoped
suite locally with `bin/ci-local --scope` (same selector as CI — one source of
truth). That scoped path is what the cloud agent's QA loop calls; see
[`recipes/environments/cloud-bootstrap.md`](recipes/environments/cloud-bootstrap.md)
for the cold/warm bootstrap budget and the cached, locked install.

When you rewrite a module, **re-level its tests in the same PR** (keep public-
behavior tests as the contract; drop internals-pinning tests; collapse duplicates
into parametrized cases). Don't gut a module's tests in a separate PR ahead of
its rewrite.

---

## The validation contract (what an agent can rely on)

| Command | Guarantee |
|---------|-----------|
| `bin/ci-local` | All locally-runnable checks (ruff check + format, mypy on `lib/vibe/`, full pytest, gitleaks, project hooks). Exit 0 ⇒ safe to push. Missing tools **skip**, never fail. |
| `bin/ci-local --fast` | Same, minus slow frontend tests — for tight inner loops. |
| `bin/ci-local --scope [paths]` | Pytest scoped to changed modules (auto-diff vs `origin/main`, or the explicit paths). Same `testscope.py` selector as CI; the cloud agent's QA path. Lint/secret scans still run whole-tree. |
| `python -m lib.vibe.testscope <paths>` | Prints exactly which suites CI will run (`ALL` / paths / empty). |
| `bin/<cli> --help` + live smoke test | CLI behavior proof (live runs only). |

Minimal bootstrap: Python ≥3.11, then install the pinned, cacheable closure —
`uv pip sync requirements.lock && uv pip install -e . --no-deps` (or, without uv,
`pip install -r requirements.lock && pip install -e . --no-deps`). No service
account or network beyond the package index needed to validate a change locally.
Regenerate the lock after a `pyproject.toml` deps change:
`uv pip compile pyproject.toml --extra dev --generate-hashes -o requirements.lock`.

---

## Agent-authored PR contract (revamp period)

Every PR opened by a coding agent during the revamp must state, in its
description:

1. **What changed and why** — 3-5 bullets.
2. **The staged step** — which non-destructive migration step this is (reference
   the plan doc's sequence), and what is intentionally left for later.
3. **Test proof** — the exact local commands run and their results. CLI changes
   include a per-subcommand live smoke-test matrix (✅ pass / ❌ fail / ⏸️ deferred);
   ⏸️ requires a follow-up ticket.
4. **Isolation confirmation** — that modules you touched still run and test in
   isolation, and that new cross-module tests live in `tests/integration/` only
   at real seams.
5. **Sync confirmation** — that `.coderabbit.yaml`, this file, and the plan doc
   (+ its Linear summary) were updated if the change touched structure,
   run/validation flow, testing strategy, or the agent-PR contract — OR an
   explicit note that none of those were affected.

**CodeRabbit is a guardrail, not a roadblock.** It defaults to **approve**: once
nothing blocking remains, it approves even with open non-blocking nitpicks. A
finding **blocks only if future PRs will build on top of it** (the cost compounds
if it merges as-is) — fix those before merge. Concretely, **CodeRabbit should
request changes when:** behavior changes ship without tests; CLI changes lack a
live smoke-test matrix; coupling increases or module seams blur (reach-through,
new globals); an integration test mocks the collaborator instead of the boundary;
a structural change skips the sync rule; local run/validation is broken or slowed;
or the PR is a big-bang rewrite where staged extraction was viable. Everything
else — one-off internals, style, naming, micro-opts, out-of-scope cleanup — is a
non-blocking nitpick: surface it, file a follow-up if worth keeping, approve
anyway. (A thin PR *description* is a warning, not a block; the substance behind
the contract — tests, isolation, the sync edit — is what blocks.) Full criteria:
[`docs/review/coderabbit-policy.md`](docs/review/coderabbit-policy.md).

**A human should still intervene for:** subjective product/UX/branding calls,
secret values, external-account actions, and anything ambiguous enough that the
right architecture isn't clear from the ticket. See the HUMAN-ticket guidance in
[`docs/archive/CLAUDE.boilerplate.md`](docs/archive/CLAUDE.boilerplate.md).

Review policy details and a worked PR example:
- [`docs/review/agent-ready-rubric.md`](docs/review/agent-ready-rubric.md) — **the
  `agent-ready`/`needs-scoping`/`wall`/`gate` label contract and dependency-hygiene rules**
- [`docs/review/triage-intelligence.md`](docs/review/triage-intelligence.md) — **the
  triage operating model on top of the rubric: taxonomy, the Linear Triage
  Intelligence guidance text, and the board-quality → CLAUDE.md feedback loop**
- [`docs/review/external-service-milestone-pattern.md`](docs/review/external-service-milestone-pattern.md) — **the
  reusable milestone + ticket-graph shape for any milestone that integrates an external provider**
- [`docs/review/coderabbit-policy.md`](docs/review/coderabbit-policy.md)
- [`docs/review/agent-pr-example.md`](docs/review/agent-pr-example.md)

Cloud execution of this contract (the agent that *runs* the loop, not just the
rules):
- [`docs/architecture/VIBE-140-cloud-coding-environment.md`](docs/architecture/VIBE-140-cloud-coding-environment.md)
  — **the cloud coding environment program** (Cursor Cloud bridge → self-hosted
  Claude Code runner on Fly.io; matched-pair Linear projects)
- [`.claude/commands/pr-autopilot.md`](.claude/commands/pr-autopilot.md) +
  [`recipes/workflows/pr-autopilot.md`](recipes/workflows/pr-autopilot.md) — **the
  PR-autopilot loop** the runner executes after opening a PR (wait for CodeRabbit
  + CI, fix CI/conflicts, work ahead on blockers as draft PRs to `main`, escalate
  to Slack, hold open ≤90 min until merged; runner-path commits/PRs are
  de-attributed)

---

## Walls & gates (milestone discipline)

Every milestone is bracketed by two control tickets, and **all milestones get
both.** This is how multi-agent work stays scoped and verifiable without
interpretation drift.

- **Wall — the milestone's entrance.** The *first* ticket. It scopes the
  milestone, validates the plan and assumptions, and **sets the acceptance
  criteria** for the rest of the work. Nothing else in the milestone starts
  until the wall clears. Title `[Wall] <project> — <milestone> … cleared`;
  label `wall`.
- **Gate — the milestone's exit.** The *last* ticket. It validates the work and
  **confirms every acceptance criterion the wall set has been met.** The
  milestone is done only when its gate is Done. Title
  `[Gate] <project> — <milestone> complete`; label `gate`.

**Wiring (mechanical — use `bin/ticket relate`; never paraphrase a dependency in
prose where an edge belongs):**

1. The **wall blocks every other ticket** in its milestone — the work tickets
   *and* the gate. Work cannot begin until the wall is Done.
2. **Every work ticket blocks the gate.** The gate's blocker set *is* the
   milestone's definition of done — wire late-added tickets in too.
3. **Across milestones, chain at the milestone level:** the downstream
   milestone's **wall is `blocked-by` the upstream milestone's gate.** Keep the
   cross-boundary graph shallow; add a direct ticket→ticket edge only for a
   real, narrow dependency.
4. **A blocker is only real when work genuinely cannot proceed.** Don't encode
   soft "nice to do first" ordering as a blocker — it needlessly serializes
   parallel agents.

**Lifecycle:** walls go first, gates go last; everything between them runs in
parallel across distinct surfaces. Close a wall once its scope/contract is set
and verified (or the user gives explicit go-ahead to proceed — record it in a
wall comment). Close the gate **last**, only when every blocker is Done,
validation passed, and docs are updated. Any human-only step (secrets, OAuth,
billing, sign-off) gets its **own** ticket — never buried in an implementation
ticket.

> **VIBE convention:** *every* milestone carries a wall (it is the scoping +
> acceptance-criteria step), which is intentionally broader than the PROMPT
> team's "wall only when a hard blocker exists" model; gates are mandatory
> everywhere. Full detail: the canonical Linear doc *"Dependency walls and
> gates."*

**External-service milestones** (any milestone that integrates a provider — Fly,
Neon, Axiom, GitHub Actions, a model provider, …) have a repeating internal shape
on top of this discipline: a docs-index → CLI-installer → guided-human-setup lane
per provider, a shared repo-stored docs index, and a doc-drift → `HUMAN ‼️`
contract. Don't re-derive it — follow
[`docs/review/external-service-milestone-pattern.md`](docs/review/external-service-milestone-pattern.md)
(scaffold with `/new-milestone`).

---

## Critical path to packaged PR Autopilot in DEAL

The revamp's structure choices exist to make the **PR-autopilot capability**
(agent-PR contract + review firewall + module-scoped validation) extractable as a
package DEAL can install:

1. **Module contract** → packages have explicit surfaces and declared deps, so
   autopilot-relevant modules can be lifted without the whole repo.
2. **Two-level testing** → an extracted package ships with suites that run in
   isolation *and* prove its seams.
3. **Validation contract** → `bin/ci-local` + module-scoped CI is the reusable
   "does this change pass?" gate the autopilot leans on.

Physical extraction/packaging is owned by the **VIBE-86 line** and the publish
milestone (**VIBE-83/88**), not by structural PRs. See the plan doc §7.

The **runtime** that exercises this capability — a remote, Slack/Linear-triggered
agent that opens PRs into the gate and drives them to merge — is the
[cloud coding environment program](docs/architecture/VIBE-140-cloud-coding-environment.md)
(VIBE-140; Cursor Cloud bridge today, self-hosted Claude Code on Fly.io next). The
PR-autopilot loop it runs is what DEAL ultimately installs alongside the packaged
contract.

---

## Operating rules (condensed — full detail in the archive)

- **Work on a fresh worktree.** "Do ticket VIBE-123" = `bin/vibe do VIBE-123`;
  do the work in the worktree, open a PR when done. Never work in the main
  checkout.
- **Every PR references its ticket** in the title (`VIBE-123: ...`) and carries a
  **risk label** (Low/Medium/High) plus type and area labels.
- **PRs target `main` — always.** A PR's base branch is `main`, never another
  feature branch. If the work is bundled on top of a not-yet-merged PR (it depends
  on code from an earlier ticket), open it as a **draft** with the **`DNM`** (do
  not merge) label, and state — in **both** the PR description **and the ticket** —
  that it depends on the earlier ticket's work and must wait for that PR to merge
  first. When the parent merges: rebase onto `main` (dropping the already-merged
  commits), retarget the base to `main`, drop `DNM`, and un-draft. A PR based on a
  feature branch is never a valid *final* state.
- **Rebase, never merge** main into a feature branch. Force-push only feature
  branches, never main.
- **CLI doctrine** (`agent_instructions/CLI.md`): smoke-test every subcommand
  locally before a CLI PR; maximalist surface + same-PR docs; classify every CLI
  error (agent's fault → memory file; CLI's fault → run `bin/ticket
  file-tooling-issue`, which files an Urgent `Bug`+`DX` ticket and de-dups it —
  the `PostToolUse` hook auto-files it on a `VIBE_TOOLING_FAULT` crash marker).
- **Read before editing; match existing patterns; keep changes minimal;** don't
  commit secrets; don't skip CI.
- **Run `bin/ci-local` before pushing.**
- **Linear priority is a field, not a label** (Urgent/High/Medium/Low). Don't use
  P0–P3 labels. **Linear is the only supported tracker** during the revamp.

For the exhaustive command reference, label tables, recipe index, and integration
wizard list, see [`docs/archive/CLAUDE.boilerplate.md`](docs/archive/CLAUDE.boilerplate.md).
