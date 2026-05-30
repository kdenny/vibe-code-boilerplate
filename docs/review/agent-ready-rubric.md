# Agent-Ready Rubric — VIBE board scoping contract

> **Status: live (authored during VIBE-175, 2026-05-30).** This is the canonical
> definition of what the `agent-ready`, `needs-scoping`, `wall`, and `gate`
> labels mean on the VIBE board, and the bar a ticket must clear before a coding
> agent is pointed at it. It is referenced from [`CLAUDE.md`](../../CLAUDE.md).
> VIBE-178 (board discipline brief) folds this into the broader operating brief;
> this doc is the precise label contract underneath it.

The board is an **agent execution queue**. A label is a promise about what
happens when an agent (or a human) pulls the ticket. The promise has to be
trustworthy or the queue stops being useful: an agent that pulls a ticket
labelled `agent-ready` and then has to invent a missing contract wastes a loop
and usually ships the wrong thing. This rubric exists so the labels mean exactly
one thing each.

---

## The one-line test for each label

| Label | One-line test |
|---|---|
| **`agent-ready`** | A competent coding agent can pick this up and finish it **without making an unanswered design decision** — the only thing standing between "now" and "done" is its declared blockers clearing. |
| **`needs-scoping`** | Doing this well still requires a **decision a human or a scoping pass must make first**. There is at least one open design question whose answer changes the implementation. |
| **`wall`** | A **decision checkpoint** that must be *locked* before the tickets behind it become real agent-ready work. A wall clears by recording decisions, not by writing code. |
| **`gate`** | An **end-to-end validation checkpoint** that confirms a milestone's work actually composes and works, proven not asserted. A gate clears by running a validation matrix, not by writing the feature. |

`agent-ready` is about **design certainty**, not **unblocked-ness**. A ticket can
be `agent-ready` and still blocked by three other tickets — that is fine and
common. What it may **not** be is `agent-ready` with an open question about *what
to build* or *what contract to build against*.

---

## `agent-ready` — the bar

A ticket earns `agent-ready` only when **all** of these hold:

1. **Unambiguous target.** One sentence stating what "done" produces. If you
   can't write it, the ticket isn't ready.
2. **Implementation plan.** The concrete shape of the change — files/surfaces
   touched, the approach — at a level an agent doesn't have to reverse-engineer.
3. **Acceptance criteria that are checkable.** Each criterion is something an
   agent can verify it met (a test passes, a command behaves, a file exists with
   a given shape). "Works well" is not a criterion.
4. **Validation/test expectation.** How the change is proven locally
   (`bin/ci-local`, a smoke matrix, specific fixtures). CLI changes name the
   per-subcommand smoke test.
5. **No unresolved design decision.** Every fork in the road is decided in the
   ticket or in a named upstream ticket/doc. If the agent would have to choose
   between materially different architectures, it is `needs-scoping`.
6. **Real, declared dependencies.** Anything the work genuinely needs first is
   wired as a `blocked-by` edge — including *foundational contracts* (a config
   model, a CLI framework, a pattern definition). A hidden dependency is the most
   common way a ticket is falsely `agent-ready`.
7. **Context is reachable, not assumed.** Source links (GitHub PR/issue),
   strongest cross-repo references (`DEAL-*`/`LIFT-*`/`PROMPT-*`), and the
   relevant Linear Doc are linked in the body — not left in someone's head.

The canonical well-formed `agent-ready` ticket carries these sections: **Source**,
**Agent execution target**, **Implementation plan**, **Acceptance criteria**,
**Agent handoff notes**, **Suggested validation**, **Cross-repo audit notes**.
VIBE-17 is the reference example.

### Demote to `needs-scoping` when you see

- The ticket depends on a **contract/framework/format that does not exist yet**
  and is not pinned in a named upstream ticket (e.g. "use the CLI install
  framework" when no install framework is specified).
- Acceptance criteria are **aspirational** ("feels good", "is elegant") with no
  checkable form.
- The body **lists choices** without deciding them, or an agent would have to
  pick package boundaries / adoption modes / schemas to proceed.
- The ticket is a **thin stub** (intent only) for non-trivial work — no plan, no
  criteria, no validation.
- "Done" depends on a **human-only or external-account step** that isn't
  separated out (use `blocked-by-external-setup` + a guided human ticket).

When you demote, **enrich, don't just relabel**: write the explicit *outstanding
questions* into the body (a "Open questions / must resolve" list), state which
named ticket or pass will answer them, and wire the `blocked-by` edge. A
`needs-scoping` ticket should make the path back to `agent-ready` obvious.

---

## `needs-scoping` — the bar

A good `needs-scoping` ticket is a **scoping work item**, not a shrug. It carries:

- An explicit **"intentionally `needs-scoping`"** note so nobody mistakes it for
  ready work.
- **Required decision outputs** — the list of decisions the pass must produce.
- **Open questions to resolve** — the actual forks.
- Where helpful, the **menu branches** an agent should later surface as an
  interactive choice (adoption mode / package shape / trust boundary).
- **Cross-repo evidence pointers** — which repo is the strongest reference for
  each decision.

VIBE-50 and VIBE-52 are the reference examples. The output of a `needs-scoping`
pass is what lets the implementation tickets flip to `agent-ready`.

---

## `wall` and `gate` — checkpoints, not features

**Wall** (locks a contract *before* the work):
- Clears by **recording decisions**, then making the downstream tickets reflect
  them. Body holds the *locked decisions* and *out-of-scope* list.
- The tickets a wall guards should not be treated as `agent-ready` until the wall
  is cleared — the wall is what makes their design certain.
- VIBE-83 and VIBE-127 are the reference examples.

**Gate** (validates a milestone *after* the work):
- Clears by running an **explicit validation matrix** — proof, not paper
  (VIBE-89: "closes only after `0.1.0` actually publishes and clean-installs").
- A gate is itself `agent-ready` **only if it spells out the validation matrix**:
  the concrete checks, across the concrete repo/env shapes, with pass/fail
  criteria. A gate that only says "validate X end to end" is **under-specified**
  — enrich it with the matrix before trusting the label.
- A gate is never *startable* until its milestone's tickets are done (it is
  `blocked-by` them), so a gate carrying `agent-ready` is a statement about its
  *spec quality*, not its readiness to start now.

---

## Dependency & parallelism hygiene (quality barometers)

Maximum safe parallelism comes from getting edges **right**, in both directions.
Two failure modes, both worth fixing:

- **False serialization** — `A blocks B` when B doesn't actually consume A's
  output. Wastes wall-clock; agents idle behind a phantom dependency. Remove it.
- **False parallelism** — B *does* consume A's output (a config contract, a
  shared file, a base abstraction) but no edge exists. Two agents collide or one
  reworks on top of the other. Add the edge.

Rules:

1. **Foundation-first.** The ticket that defines a shared contract/format/seam
   blocks the tickets that consume it. Within a milestone, the
   "define the contract" ticket blocks the "consume the contract" tickets.
2. **One foundation, many thin consumers.** When the same framework would be
   re-specified N times (once per integration/provider), specify it **once**
   upstream and make the per-integration tickets thin consumers blocked on it —
   don't label N copies `agent-ready` as if each invents the framework.
3. **Walls gate readiness, not just order.** Downstream tickets behind an
   uncleared wall are `needs-scoping`/blocked, not `agent-ready`.
4. **Independent siblings stay unblocked.** If two tickets in a milestone share
   no artifact, do **not** chain them — let them run concurrently.
5. **Tag genuinely-parallel batches** with `parallelization` and human/external
   handoffs with `blocked-by-external-setup` / `HUMAN ‼️` so the queue is
   legible at a glance.
6. **Verify relations via the Linear GraphQL API**, not `bin/ticket get` — the
   latter renders blocking relations as self-references (known tooling bug; see
   VIBE-83 wall notes). VIBE-2 tracks the fix.

---

## Quick audit checklist (per ticket)

```
[ ] Target sentence exists and is unambiguous
[ ] Implementation plan present (not just intent)
[ ] Acceptance criteria are checkable
[ ] Validation/test expectation stated
[ ] No open design decision left to the agent
[ ] All real dependencies wired as blocked-by (incl. foundational contracts)
[ ] Source + strongest cross-repo refs + relevant Linear Doc linked
[ ] If gate: validation matrix is concrete
[ ] If wall: locked decisions recorded
→ all checked  → agent-ready
→ any design decision open → needs-scoping (+ write the open questions, wire the edge)
```
