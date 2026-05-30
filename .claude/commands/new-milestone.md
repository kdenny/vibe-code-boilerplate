---
description: Scaffold an external-service milestone (wall, provider lanes, gate) per the reusable pattern
---

# /new-milestone - Scaffold an external-service milestone

Generate the milestone shape and ticket graph for a milestone that integrates one
or more **external providers**, applying the canonical pattern so every such
milestone comes out the same way.

> **This is a thin driver.** The full spec — graph, edges, labels, docs-index and
> doc-drift contracts — lives in
> [`docs/review/external-service-milestone-pattern.md`](../../docs/review/external-service-milestone-pattern.md).
> Read it first; this command just walks you through applying it. Labels follow
> [`docs/review/agent-ready-rubric.md`](../../docs/review/agent-ready-rubric.md).

## Usage

```
/new-milestone "PR automation"            # scaffold a milestone by name
/new-milestone                            # interactive: ask for project, milestone, providers
```

## What it does

1. **Confirm scope at the wall.** Identify project `P`, milestone `M`, and the
   provider list `P₁…Pₙ`. Create `[Wall] P — M scope cleared` (label `wall`) and
   record the locked decisions (providers, install UX, acceptance criteria) in it.
2. **Wire the cross-milestone edge.** Resolve the upstream milestone, find its
   single `gate`-labelled ticket via the Linear GraphQL API, and set the new
   wall **blocked-by that gate** (see §3 rule 6 of the pattern).
3. **Ensure the shared foundation.** If the repo-backed docs index (F1) and the
   doc-drift automation (F2) tickets/implementation don't yet exist, create them;
   otherwise reference the existing ones. F1 blocks every Index ticket.
4. **Emit one lane per provider:** `Index <Pᵢ>` → `Add CLI installer flow for
   <Pᵢ>` → `Add guided human setup flow for <Pᵢ>`, chained `blocked-by` in that
   order, with the human-setup ticket carrying `blocked-by-external-setup` and
   sitting immediately before the gate.
5. **Create the gate.** `[Gate] P — M complete` (label `gate`), `blocked-by`
   every work ticket, with an explicit validation matrix that includes the
   synthetic-drift → `HUMAN ‼️` check.
6. **Label per the rubric.** `agent-ready` only where design is certain; otherwise
   `needs-scoping` with an Open-questions list and the path back to ready. Never
   leave a lane ticket ambiguous.
7. **Verify the graph** with the Linear GraphQL API (not `bin/ticket get`), and
   wire all edges with `bin/ticket relate`.

## Output

A fully-wired milestone subgraph on the board, plus a summary of the tickets
created and the edges set. Follow the checklist in §10 of the pattern doc before
declaring the milestone scaffolded.
