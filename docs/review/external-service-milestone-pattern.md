# External-Service Milestone Pattern — reusable milestone + ticket-graph shape

> **Status: live (authored for VIBE-141, 2026-05-30).** This is the canonical,
> opinionated pattern for constructing a **milestone that integrates one or more
> external providers** (Fly, Neon, Axiom, GitHub Actions, a model provider, …) on
> the VIBE board. It specializes the generic wall/gate discipline in
> [`CLAUDE.md`](../../CLAUDE.md) ("Walls & gates") and enforces the label contract
> in [`agent-ready-rubric.md`](agent-ready-rubric.md). The `/new-milestone` skill
> ([`.claude/commands/new-milestone.md`](../../.claude/commands/new-milestone.md))
> is the executable entrypoint that applies this pattern; this doc is the spec it
> follows. Apply it whenever a Future-Improvements milestone depends on an external
> service — so the milestone shape, ticket set, and dependency edges come out the
> same every time instead of being re-derived by hand.

The problem this solves: an external-service milestone has a **repeating internal
shape** — for every provider you index its docs, build a CLI install step, and add
a guided human-setup step, then validate the whole thing at a gate. Left to
improvisation, each provider lane gets invented differently, the cross-provider
contracts (docs index, drift handling, human handoff) get re-specified N times
(false parallelism), and labels drift. This pattern fixes the shape once.

---

## 1. The canonical milestone graph

For a milestone **M** in project **P** that integrates providers `P₁…Pₙ`:

```
            ┌──────────────────────────────────────────────────────────┐
 upstream   │  [Wall] P — M scope cleared            (label: wall)      │
  gate  ───▶│     blocks every ticket below, incl. the gate            │
            └───────────────┬──────────────────────────────────────────┘
                            │
   ┌────────────── shared foundation (milestone-spanning, build once) ──────────────┐
   │  F1  Build repo-backed provider docs index   (the registry + schema + check)    │
   │  F2  Auto-create HUMAN ‼️ issues for provider doc drift  (the drift automation) │
   └───────────────┬─────────────────────────────────────────────────────────────────┘
                   │  F1 blocks every Index ticket; F2 enables the drift contract
        ┌──────────┴───────── one lane per provider Pᵢ ──────────┐
        │  Index Pᵢ docs   ──blocks──▶  CLI installer Pᵢ          │
        │   (agent-ready)               ──blocks──▶  Guided human │
        │                                            setup Pᵢ     │
        │                                            (immediately │
        │                                             before gate)│
        └──────────────────────────────┬─────────────────────────┘
                                        │ every work ticket blocks the gate
            ┌───────────────────────────▼──────────────────────────────┐
            │  [Gate] P — M complete                 (label: gate)      │
            │     blocked-by every ticket above; clears by matrix       │
            └──────────────────────────────────────────────────────────┘
```

Edges are **mechanical** — wire them with `bin/ticket relate`, never paraphrase a
dependency in prose where an edge belongs (CLAUDE.md walls&gates rule). Verify the
resulting graph with the **Linear GraphQL API**, not `bin/ticket get` (it renders
blocking relations as self-references — VIBE-2).

---

## 2. The standard issue set

Every external-service milestone generates exactly these ticket types. The
per-provider lane (Index → Installer → Human-setup) repeats once per provider; the
wall, gate, and shared-foundation tickets appear once per milestone.

| # | Ticket | One per | Purpose | Default label | Key edges |
|---|--------|---------|---------|---------------|-----------|
| Wall | `[Wall] P — M scope cleared` | milestone | Lock the provider list, the install UX, and the acceptance criteria. | `wall` | **blocks** every ticket in M (work + gate); **blocked-by** upstream milestone's **gate** |
| F1 | `Build repo-backed external provider docs index` | milestone (or once for P) | The `.vibe/provider-docs-index.json` registry, its schema, and the freshness/doctor check that reads it. | `agent-ready` | **blocks** every Index ticket |
| F2 | `Auto-create HUMAN ‼️ issues for provider doc drift` | milestone (or once for P) | The automation that turns a detected doc-drift into a `HUMAN ‼️`-labelled Linear issue. | `agent-ready` | **blocked-by** F1 |
| Index Pᵢ | `Index provider docs for <Pᵢ> install` | provider | Populate the docs index for Pᵢ: every feature → docs-url + local ref + content signature. | `agent-ready` | **blocked-by** F1; **blocks** Installer Pᵢ |
| Installer Pᵢ | `Add CLI installer flow for <Pᵢ>` | provider | The menu-driven / multi-select install step for Pᵢ (a `vibe/wizards/*` consumer). | `agent-ready` | **blocked-by** Index Pᵢ; **blocks** Human-setup Pᵢ |
| Human-setup Pᵢ | `Add guided human setup flow for <Pᵢ>` | provider | The guided human step (OAuth, secrets, billing) that **sits immediately before the gate**. | `agent-ready` + `blocked-by-external-setup` | **blocked-by** Installer Pᵢ; **blocks** the gate |
| Gate | `[Gate] P — M complete` | milestone | Validate the milestone end-to-end via an explicit matrix. | `gate` | **blocked-by** every work ticket in M |

> F1/F2 are written **once** and reused across milestones. After the first
> external-service milestone builds them, later milestones reference the existing
> F1/F2 tickets (or their merged implementation) instead of regenerating them —
> the pattern emits them only when the registry/automation does not yet exist.

---

## 3. Dependency rules (the edges, precisely)

These extend the generic CLAUDE.md walls&gates wiring with the provider-lane
specifics. The two failure modes from the rubric — **false serialization** (a
phantom blocker) and **false parallelism** (a missing consume edge) — both apply;
get every edge right in both directions.

1. **Wall blocks everything in M**, including the gate and the shared-foundation
   tickets. Nothing in M starts until the wall clears.
2. **Foundation-first: F1 blocks every Index ticket.** An Index ticket *writes
   into* the registry F1 defines; without F1's schema it would invent the format.
   This is the one-foundation-many-consumers rule applied to the docs index.
3. **The Index ticket blocks the CLI installer ticket.** *This is the explicit
   "docs-index blocks CLI setup" logic.* The installer consumes the indexed
   feature → docs-url map to know **what** to install and **which** docs to verify
   its steps against. An installer built before its provider is indexed would
   hard-code URLs and drift silently — so the installer is `blocked-by` its Index
   ticket, never parallel to it.
4. **The installer blocks the guided human-setup ticket**, which **blocks the
   gate** and is the *last* work ticket before it. Human setup is the handoff that
   can only happen after the machine-side install exists.
5. **Every work ticket blocks the gate** (CLAUDE.md rule 2). The gate's blocker
   set *is* M's definition of done — wire late-added lanes in too.
6. **Across milestones, chain at the milestone level** (CLAUDE.md rule 3): M's
   **wall is `blocked-by` the upstream milestone's gate.** To find that gate,
   resolve the upstream milestone (Linear `previousMilestone`/project ordering or
   the explicit "blocked-by upstream gate" note in the wall) and locate its single
   `gate`-labelled ticket — *this is how the pattern identifies the relevant gate
   from an adjacent milestone and applies the cross-wall blocking edge.* Keep the
   cross-boundary graph shallow: one wall→gate edge, not a mesh of leaf edges.
7. **Independent provider lanes stay unblocked from each other.** Lane Pᵢ and lane
   Pⱼ share only F1/F2 and the wall/gate — never chain them, so agents run lanes
   concurrently.

---

## 4. Labeling: agent-ready vs needs-scoping

Labels follow [`agent-ready-rubric.md`](agent-ready-rubric.md) verbatim —
`agent-ready` means **no open design decision**, not unblocked-ness; a lane ticket
can be `agent-ready` *and* blocked behind its Index/Installer or behind the wall.
The defaults in §2 hold **only when** the generated ticket clears the rubric bar.
Per ticket type:

- **Index Pᵢ → `agent-ready`** when the provider and its in-scope feature set are
  decided and the F1 registry format is pinned (the schema this doc ships). It is a
  thin consumer: fill known features into a known schema.
- **Installer Pᵢ → `agent-ready`** when it builds to the install-flow contract
  (§6) — the standard index-driven, menu-driven flow over the existing
  `vibe/wizards/*` framework — and the Index ticket is wired as its blocker.
  If the provider's adoption mode or which features install is *undecided*, it is
  **`needs-scoping`**.
- **Human-setup Pᵢ → `agent-ready` + `blocked-by-external-setup`** when it produces
  the handoff-state contract (§7) and the human steps (which secret, which OAuth
  scope, which billing toggle) are enumerable. If the steps depend on an undecided
  product/trust call, **`needs-scoping`**.
- **Gate → `agent-ready` only if the validation matrix is spelled out** (rubric:
  a gate that only says "validate X end to end" is under-specified).

**Agent-ready issue-writing guidance.** Generate each lane ticket with the rubric's
canonical sections — **Source, Agent execution target, Implementation plan,
Acceptance criteria, Agent handoff notes, Suggested validation, Cross-repo audit
notes** — filled from the provider's indexed docs and the milestone wall's locked
decisions. When enough context exists, the ticket should be implementation-ready,
not a stub.

**Fallback to `needs-scoping`.** When the workflow *cannot* produce an actionable
spec for a lane ticket — an open fork the wall didn't decide, a dependency on a
contract/framework not yet pinned as a `blocked-by` edge, or aspirational
acceptance criteria — emit it as `needs-scoping` instead of a falsely-ready ticket.
Do the rubric's "enrich, don't just relabel": write an **Open questions / must
resolve** list into the body, name the ticket or pass that will answer it, and wire
the `blocked-by` edge. A `needs-scoping` lane ticket must make the path back to
`agent-ready` obvious. **Never leave a lane ticket ambiguous.**

---

## 5. The provider docs index (repo-stored)

Provider reference material lives in **repo files, not Linear documents** — so it
is version-controlled, diffable, and reviewable in the same PR as the code that
depends on it. Two layers:

1. **Human-readable reference** — recipes under `recipes/integrations/<provider>.md`
   (existing convention).
2. **Machine-readable index** — `.vibe/provider-docs-index.json`, validated by
   [`.vibe/provider-docs-index.schema.json`](../../.vibe/provider-docs-index.schema.json),
   mapping **feature → docs-url** plus the drift-tracking fields. This is the
   artifact F1 builds and each Index ticket populates.

Shape (one entry per provider; one entry per feature under it):

```jsonc
{
  "providers": {
    "github-actions": {
      "milestone": "PR automation",
      "last_indexed": "2026-05-30",
      "features": {
        "pr-autopilot-token": {
          "docs_url": "https://docs.github.com/.../authenticating-with-a-github-app",
          "local_ref": "recipes/integrations/github-actions.md",
          "content_signature": "sha256:…",   // signature of the indexed doc content
          "last_verified": "2026-05-30"
        }
      }
    }
  }
}
```

**Storing & updating the feature → docs-url mapping.** Adding a provider feature =
add a `features.<key>` entry with its `docs_url`, `local_ref`, a `content_signature`
captured at index time, and `last_verified`. Updating = re-capture the signature
and bump `last_verified` (the same motion as the
[integration-freshness](../../recipes/workflows/integration-freshness.md) precedent,
which this index is the docs-aware sibling of). The mapping is **only** edited via a
PR, so every change to what the install flow believes about a provider is reviewed.

---

## 6. The install-flow contract (what CLI-installer tickets consume)

The installer lane is the standard **menu-driven, index-driven** install flow —
not a hand-written wizard per provider. 141 pins its *shape* so every installer
ticket is a thin consumer; the *elegant DX implementation* of the abstraction is
owned by **VIBE-179** (installer tickets are design-certain against this contract
and remain transitively blocked on 179's implementation, never on an open design
question).

The contract an installer ticket builds to:

- **Module registry.** Each milestone module registers a single entry the CLI
  iterates: `{ id, label, providers[], wizard_entrypoint, required_index_keys }`.
  `setup.py` discovers modules from the registry — it does **not** hard-code them.
- **Selection UX.** Use the existing primitives in `vibe/ui/components.py`:
  `NumberedMenu`/`SelectOption` for single-select (pick the module), `MultiSelect`
  for the **multi-select / checkbox** provider-and-feature choices. This is the
  "Claude Code–style menu" the milestone source discussion calls for.
- **Index-driven rendering.** Provider choices, prerequisites, and reference links
  are rendered **from `.vibe/provider-docs-index.json`** (§5), never hard-coded —
  this is *why* the Index ticket blocks the installer (§3 rule 3).
- **Branch to the provider wizard.** Each selected provider branches into its
  `vibe/wizards/<provider>.py` path.
- **Defer human-only steps.** Anything requiring a provider console (OAuth,
  secrets, billing) is **kept out of the install path** and handed to the guided
  human-setup flow (§7) — the installer's job ends at the machine-side install.

## 7. The human-handoff state contract (what guided-setup tickets produce)

The guided human-setup flow is the *last* work before the gate, and it must leave
the milestone in a state the gate can validate **without hidden assumptions**. 141
defines that handoff-state contract once, so all nine milestones share one shape
instead of inventing it nine times.

- **File.** The flow writes `.vibe/handoff-state.json` (layered `.vibe/*` artifact
  convention), validated by
  [`.vibe/handoff-state.schema.json`](../../.vibe/handoff-state.schema.json).
- **Shape.** Per milestone + provider, a list of human steps, each:
  `{ id, description, where (console|secret|oauth|billing), status
  (pending|done|blocked|waived), required, secret_ref }`. **Secrets are references, never values**
  (`"gh:ANTHROPIC_API_KEY"`), so the committed file is safe.
- **Gate reads it.** The gate's validation matrix asserts every *required* human
  step is `done` (or explicitly waived) before the milestone closes — that is how
  the handoff reaches validation deterministically.
- **HUMAN ‼️ tie-in.** Guided-setup tickets carry `blocked-by-external-setup` +
  `HUMAN ‼️` because their steps bottom out in human actions in provider consoles.

## 8. Doc-drift contract (when to log, when to open an issue, and the HUMAN ‼️ guarantee)

Drift = a provider doc the install flow depends on has changed underneath us.
Detection piggybacks the freshness machinery (the `bin/vibe doctor` check + the
monthly GitHub Action that already exist for integration-freshness): for each
indexed feature, compare the **current** doc's signature against the stored
`content_signature`, and check `last_verified` against the freshness window
(default 30 days).

**When to only log vs. open a new issue** — this fork is explicit:

- **Log only (no issue).** The routine path: re-verification confirms the
  signature is unchanged, or only the freshness clock ticked. Update
  `last_verified` in the index (a chore-level commit). No human action is needed,
  so no issue is created — this avoids drowning the board in noise.
- **Open a new Linear issue automatically.** The signature **changed** — the doc
  materially differs from what the installer/human-setup was built against, which
  can silently break a setup. F2's automation **creates a new issue** (it does not
  merely append a log line), titled for the provider + feature, carrying the old →
  new signature, the `docs_url`, and a link to the affected lane tickets, filed
  under the milestone (or a standing "provider doc drift" area).

**The HUMAN ‼️ guarantee.** *Every* issue F2 opens for real drift **must** carry
the **`HUMAN ‼️`** label — a person has to look at the changed provider doc and
decide whether the install flow needs updating; an agent must not silently re-index
over a breaking change. Attaching `HUMAN ‼️` is part of F2's create call, not an
afterthought, and the **gate's validation matrix asserts it**: a synthetic
signature change must produce exactly one new `HUMAN ‼️`-labelled issue. (This is
the docs-drift analogue of the integration-freshness Action's `HUMAN` GitHub issue,
and mirrors the cross-team LIFT-594/595 contracts.)

---

## 9. Worked example — the "PR automation" milestone

Instantiating the pattern for **PR automation** (providers: GitHub Actions, +
Linear / CodeRabbit as the PR-policy surface), mapped onto the current board:

| Pattern role | Ticket |
|---|---|
| Wall | the milestone's `[Wall]` ticket — locks providers + install UX |
| F1 (docs index) | `Build repo-backed external provider docs index` (cf. LIFT-594) |
| F2 (drift automation) | `Auto-create HUMAN ‼️ issues for provider doc drift` (cf. LIFT-595) |
| Index | **VIBE-149** Index provider docs for PR automation install |
| Installer | **VIBE-158** Add CLI installer flow for PR automation |
| Human-setup | **VIBE-167** Add guided human setup flow for PR automation |
| Gate | the milestone's `[Gate]` ticket — runs the validation matrix |

Edges: Wall → 149/158/167 + gate; F1 → 149; 149 → 158 → 167 → gate. Each of the
nine providers on the board (Secrets, Logs & Axiom, PR automation, Calendar &
Meetings, PostHog, LLM toolkit, GitHub Actions, Fly.io, Neon) has the same
Index → Installer → Human-setup triple (147–155 / 156–164 / 165–173, provider-aligned
by offset), all rooted through this pattern (`VIBE-84/179 → VIBE-141 → Index →
Installer → Human-setup → Gate`).

---

## 10. Applying the pattern

Use `/new-milestone` (see [`.claude/commands/new-milestone.md`](../../.claude/commands/new-milestone.md)),
which walks the wall, the provider list, and emits the lane tickets with the §3
edges and §4 labels pre-wired. Or apply by hand against this checklist:

```
[ ] Wall created; blocked-by upstream milestone's gate; blocks all of M
[ ] F1 (docs index) exists or created; blocks every Index ticket
[ ] F2 (drift automation) exists or created; blocked-by F1; HUMAN ‼️ guaranteed
[ ] Each provider lane: Index → Installer → Human-setup, chained + wired to gate
[ ] Human-setup tickets carry blocked-by-external-setup; sit immediately before gate
[ ] Every lane ticket labelled per the rubric (agent-ready only if design-certain)
[ ] needs-scoping fallbacks carry Open-questions + the path back to agent-ready
[ ] Gate spells out its validation matrix (incl. the synthetic-drift → HUMAN ‼️ check)
[ ] Graph verified via the Linear GraphQL API, not bin/ticket get
```
