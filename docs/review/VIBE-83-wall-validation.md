# VIBE-83 Wall Validation — *Packaged Vibe → Publish Package*

**Ticket:** [VIBE-83 — [Wall] Packaged Vibe — Package contract and module boundaries cleared](https://linear.app/2wrist/issue/VIBE-83)
**Pass date:** 2026-05-30 · **Status of wall:** In Progress
**Stacked on:** VIBE-174 (modular restructure). Open this PR's diff against the VIBE-174 branch.

> **What a wall pass is.** Per the wall/gate discipline in `CLAUDE.md` (VIBE-180), a
> wall is *the milestone's entrance*: it scopes the contract and **blocks every
> other ticket in the milestone until it clears.** "Picking up" the wall means
> validating that (a) the locked decisions are recorded, (b) the downstream
> tickets reflect them, (c) the dependency graph obeys the wall/gate rules, and
> (d) nothing required to reach the gate is unowned. This document is the canonical
> half of that pass; the Linear tickets are the matched half.

---

## Method & data source

- Tickets read live from Linear (team `VIBE`, project *Packaged Vibe*).
- **Dependency edges taken from the GraphQL API, not `bin/ticket get`.** The CLI's
  "Blocked by" line is corrupted — it renders every ticket as blocked by *itself*
  (`inverseRelations.relatedIssue` echoes the source issue). All edges below are the
  authoritative forward `blocks` relations. *(Known issue — see Findings §F5.)*

### Authoritative milestone DAG (forward `blocks`)

```
VIBE-83  (wall, In Progress)   blocks → VIBE-179            ← only one work ticket!
VIBE-84  (Todo)                blocks → 85, 86, 88, 89, 141
VIBE-85  (Todo)                blocks → 88, 89
VIBE-86  (Todo)                blocks → 88, 89
VIBE-87  (Todo)                blocks → 88, 89
VIBE-88  (Todo)                blocks → 89
VIBE-179 (Todo)               blocks → 88, 89, 141
VIBE-89  (gate, Todo)          blocks → 95 (downstream LIFT wall)
```

Work-ticket set = {84, 85, 86, 87, 88, 179}. Gate = 89.

---

## Validation against the wall/gate rules (CLAUDE.md)

| Rule (VIBE-180) | Expected | Actual | Verdict |
|---|---|---|---|
| **R1 — wall blocks every other ticket** (work + gate) | 83 → 84,85,86,87,88,179,89 | 83 → **179 only** | ❌ **FAIL** |
| **R2 — every work ticket blocks the gate** | 84,85,86,87,88,179 → 89 | all six → 89 | ✅ PASS |
| **R3 — gate blocks the downstream wall** | 89 → next wall | 89 → 95 | ✅ PASS |
| **R3 — this wall blocked-by upstream gate** | 83 ← core-refactor gate? | none wired | ⚠️ see §F6 |

The wall's own clear-criteria ("decisions recorded **and** downstream tickets
reflect them") are otherwise met — see the coverage matrix below.

### Locked v0 decisions ↔ child-ticket coverage

| # | Locked decision (VIBE-83) | Reflected in | OK |
|---|---|---|---|
| 1 | Single private `vibe` pkg; import namespace `vibe` | 84 (surface), 85 (metadata) — but **no ticket scaffolds the namespace**, §F2 | ⚠️ |
| 2 | `uv` default; binary deferred | 85 | ✅ |
| 3 | v0 = PR automation; 4-module taxonomy = future | 84 (out-of-scope), 86 (re-scoped), 88 (future) | ✅ |
| 4 | Elegant Claude-Code DX, prototyped early | 179 | ✅ |
| 5 | Config = injected core + optional loader | 84 §3, 179 (Principle 4) | ✅ |
| 6 | Real `vibe` CLI; slashes are thin wrappers | 84 §5, 179 §1 | ✅ |
| 7 | Distribution path left open | 87 | ✅ |
| 8 | Versioning `0.1.0`, semver | 85, 89 | ✅ |
| 9 | Gate = proof, not paper | 89 DoD | ✅ |
| 10 | M1 ↔ M2 overlap allowed; wire blocks only where needed | 86, 179 (coordinate-with-M2 notes) | ✅ |

---

## Findings

### F1 — ❌ The wall does not gate its milestone (R1 violation)
VIBE-83 blocks **only VIBE-179**. VIBE-84, 85, 86, 87, 88 and the gate 89 are *not*
blocked by the wall, even though 84/85/87's bodies say "Depends on VIBE-83." Because
those tickets are already labelled `agent-ready`/Todo, an agent can legitimately pull
**VIBE-84 while the wall is still open** — exactly the "falsely agent-ready" failure
the rubric warns about. **Fix:** add wall→{84,85,86,87,88,89} blocking edges (checklist
below). This is the main thing standing between the current board and a clean wall.

### F2 — ✅ Missing "scaffold the package" ticket → filed **VIBE-182**
Resolved by VIBE-182: the repo now has a top-level `vibe/` package,
`python -m vibe`, `vibe = "vibe.cli.main:main"`, and `packages.find` includes
`vibe*`.

Before VIBE-182, VIBE-84 was a *spec* (ships no code); VIBE-85 was
*build/release config* and only listed "import package `vibe`" as metadata; and
VIBE-86 was the *integration seam*. The concrete code-move (`lib/vibe/` →
`vibe/`, fix imports, console entry) — which was also entangled with VIBE-174's
restructure — was unowned. **Action taken:** created
[**VIBE-182**](https://linear.app/2wrist/issue/VIBE-182) *(agent-ready, infra/architecture/critical-path)*:
blocked-by 83, 84, 174; blocks 85, 89.
**Follow-up:** trim VIBE-85 deliverable #1 so it stops claiming the namespace code-move
(now VIBE-182's job) and keeps only uv/build/extras/release.

### F3 — ⚠️ VIBE-179 ⇄ VIBE-84 dependency is contradictory + unwired
VIBE-179's footer says "**Depends on** VIBE-83 + VIBE-84," but its deliverable #5 says it
"**feeds into** VIBE-84 / VIBE-88," and there is **no 84→179 edge** in Linear. A prototype
that sets the DX bar should *inform* the surface spec, not depend on it. **Recommendation:**
pick one direction — treat 179 as depending on **83 only** and *feeding* 84 (preferred,
matches "prototype early"), and delete the "depends on 84" language; or, if 84 must land
first, wire 84→179. Don't leave both claims standing.

### F4 — ⚠️ (acceptable) VIBE-87 → VIBE-85 "feeds" is intentionally not a block
VIBE-87 says it wires the chosen publish step "back into VIBE-85's release workflow," but
85 explicitly leaves publish "pluggable until VIBE-87." So 85 can proceed and 87 patches it
later — **coordinate, don't block.** No change needed; recorded so it isn't mistaken for a
missing edge.

### F5 — 🔧 Tooling: `bin/ticket get` renders blocking relations as self-references
Every ticket shows `Blocked by: <itself>` (often repeated). The underlying Linear data is
fine; the bug is reading `relatedIssue` on `inverseRelations` (which points back at the
source) instead of `issue`. Worth a DX ticket since it makes the board un-trustable from the
CLI and forces a GraphQL fallback for every dependency check. *(Speed rule: a wall pass
shouldn't need a hand-written GraphQL query to see its own edges.)*

### F6 — ❓ Open: should VIBE-83 be blocked-by the core-refactor gate?
The v0 contract says packaging "rides on the core refactor reaching clean module
boundaries." VIBE-182 is blocked-by VIBE-174, but the *wall itself* has no upstream-gate
edge (R3, incoming side). If the revamp has a gate ticket, consider wiring `83 blocked-by
<revamp-gate>` so the milestone can't start ahead of the refactor. Left for a human — depends
on whether the revamp is modelled as a gated milestone.

---

## Recommended Linear actions (apply checklist)

Applied in this pass:
- [x] **Created VIBE-182** (package scaffold) and wired 83→182, 84→182, 174→182, 182→85, 182→89.

Proposed (not yet applied — board hygiene, your call):
- [ ] **R1 fix:** add wall edges `83 → 84`, `83 → 85`, `83 → 86`, `83 → 87`, `83 → 88`, `83 → 89`.
      *(Note: this will correctly mark those tickets blocked until the wall is closed.)*
- [ ] **F3:** resolve 179⇄84 — preferred: drop "depends on VIBE-84" from VIBE-179; keep 179 feeding 84.
- [ ] **F2 follow-up:** trim VIBE-85 deliverable #1 to cede the namespace code-move to VIBE-182.
- [ ] **F5:** file a DX ticket for the `bin/ticket get` self-reference bug.
- [ ] **F6:** decide whether `83` should be blocked-by a core-refactor gate.

> Edges are reconcilable in seconds (`issueRelationCreate` / delete); say the word and I'll
> apply the R1 fix and F3 in one batch.

---

## Sync-rule note
This pass adds a review/validation doc only — it does **not** touch repo structure, module
boundaries, the local run/validation flow, or the agent-PR contract, so no `.coderabbit.yaml`
change is required.
