# CLAUDE.md — VIBE Repo (Provisional, Revamp Period)

> **Status: PROVISIONAL.** This repo is being actively restructured. This file is
> the shared contract between agents and reviewers **for the duration of the
> revamp**. It is intentionally leaner than the pre-revamp instructions, which are
> archived verbatim at [`docs/archive/CLAUDE.boilerplate.md`](docs/archive/CLAUDE.boilerplate.md)
> — consult that file for the full operational detail on tickets, worktrees,
> labels, deployment wizards, and recipes. Nothing there was deleted; it was moved.
>
> This file is **hand-authored for the revamp** and is the live source of agent
> instruction during this period. Do not regenerate it from `agent_instructions/`
> until the revamp completes and this provisional notice is removed.

---

## Two standing rules (read these first)

1. **Sync rule — review config tracks the architecture.** Any substantial change
   to repo structure, module boundaries, the local run/validation flow, or the
   agent-PR contract MUST update [`.coderabbit.yaml`](.coderabbit.yaml) **in the
   same PR**. CLAUDE.md and `.coderabbit.yaml` are a matched pair. A PR that shifts
   the architecture without updating the review config is incomplete, and
   CodeRabbit is configured to request changes on it.

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
`lib/vibe/` package) that runs *alongside* a project to manage tickets, worktrees,
PR policy, and integrations. The current effort is a **non-destructive revamp**:
improve the structure into clean modular packages without breaking working
behavior, on the critical path toward packaging the review/PR-autopilot capability
for downstream adoption in **DEAL**.

---

## Migration posture: non-destructive, staged

The revamp preserves working behavior while structure improves. Every change must
respect these:

- **Preserve behavior.** Working commands keep working. Refactors are behavior-
  preserving unless the ticket explicitly says otherwise.
- **Stage, don't big-bang.** Prefer incremental extraction (move one seam at a
  time, keep it green) over sweeping rewrites. A PR that churns large surface area
  without a staged justification should be split.
- **Keep modules independently runnable and testable.** A module you touch should
  still run and be tested in isolation, not only inside the full app.
- **Integrate through explicit interfaces.** Compose modules via clear contracts,
  not hidden coupling, shared globals, or reach-through into internals.
- **Prove local validation stays fast and reliable.** New structure and tests must
  demonstrate that local run + validation remain quick and trustworthy.

## Target shape (where the revamp is heading)

- **Modular package boundaries** — clear seams, explicit contracts, low hidden
  coupling.
- **Quick local run + validation** — minimal bootstrap steps; `bin/ci-local`
  remains the one-command local check and must stay fast.
- **Tests at the right level** — module-level unit tests per module, plus
  **combinatorial / integration suites only where modules are designed to
  compose.** Don't add integration tests for modules that aren't meant to interact.
- **Clean critical path to packaged PR Autopilot in DEAL** — structure choices
  should move us toward shipping this capability downstream, not away from it.

---

## Agent-authored PR contract (revamp period)

Every PR opened by a coding agent during the revamp must state, in its description:

1. **What changed and why** — 3-5 bullets.
2. **The staged step** — which non-destructive migration step this is, and what is
   intentionally left for later.
3. **Test proof** — the exact local commands run and their results. CLI changes
   include a per-subcommand live smoke-test matrix (✅ pass / ❌ fail / ⏸️ deferred);
   ⏸️ requires a follow-up ticket.
4. **Isolation confirmation** — that modules you touched still run and test in
   isolation.
5. **Sync confirmation** — that `.coderabbit.yaml` (and this file) were updated if
   the change touched structure, run/validation flow, or the agent-PR contract,
   OR an explicit note that none of those were affected.

**CodeRabbit should request changes when:** behavior changes ship without tests;
CLI changes lack a live smoke-test matrix; coupling increases or module seams blur;
a structural change skips the sync rule; local run/validation is broken or slowed;
or the PR is a big-bang rewrite where staged extraction was viable.

**A human should still intervene for:** subjective product/UX/branding calls,
secret values, external-account actions, and anything ambiguous enough that the
right architecture isn't clear from the ticket. See the HUMAN-ticket guidance in
[`docs/archive/CLAUDE.boilerplate.md`](docs/archive/CLAUDE.boilerplate.md).

Review policy details and a worked PR example:
- [`docs/review/agent-ready-rubric.md`](docs/review/agent-ready-rubric.md) — **the
  `agent-ready`/`needs-scoping`/`wall`/`gate` label contract and dependency-hygiene rules**
- [`docs/review/coderabbit-policy.md`](docs/review/coderabbit-policy.md)
- [`docs/review/agent-pr-example.md`](docs/review/agent-pr-example.md)

---

## Operating rules (condensed — full detail in the archive)

These remain in force during the revamp. The archived boilerplate doc has the
complete versions; the essentials:

- **Work on a fresh worktree.** "Do ticket VIBE-123" = `bin/vibe do VIBE-123`,
  do the work in the worktree, open a PR when done. Never work in the main checkout.
- **Every PR references its ticket** in the title (`VIBE-123: ...`) and carries a
  **risk label** (Low/Medium/High) plus type and area labels.
- **Rebase, never merge** main into a feature branch. Force-push only feature
  branches, never main.
- **CLI doctrine** (`agent_instructions/CLI.md`): smoke-test every subcommand
  locally before a CLI PR; maximalist surface + same-PR docs; classify every CLI
  error (agent's fault → memory file; CLI's fault → Urgent ticket + DX channel).
- **Read before editing; match existing patterns; keep changes minimal;** don't
  commit secrets; don't skip CI.
- **Run `bin/ci-local` before pushing.**
- **Linear priority is a field, not a label** (Urgent/High/Medium/Low). Don't use
  P0–P3 labels.

For the exhaustive command reference, label tables, recipe index, and integration
wizard list, see [`docs/archive/CLAUDE.boilerplate.md`](docs/archive/CLAUDE.boilerplate.md).
