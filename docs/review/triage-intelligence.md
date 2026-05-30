# Triage Intelligence — VIBE board operating model

> **Status: live (authored during VIBE-177, 2026-05-30).** This is the canonical
> operating model for triaging the VIBE board: how work is classified, what
> minimum context each class needs, what Linear's **Triage Intelligence** is told
> to do, and how recurring board-quality failures feed back into
> [`CLAUDE.md`](../../CLAUDE.md). It sits **on top of** the
> [agent-ready rubric](agent-ready-rubric.md): the rubric defines what the
> `agent-ready` / `needs-scoping` / `wall` / `gate` labels *mean*; this document
> defines the *system that applies and maintains them continuously* and the bar a
> ticket must clear before broad, hands-off agent execution.
>
> Scope boundaries: [VIBE-178](https://linear.app/2wrist/issue/VIBE-178) condenses
> the broader board context into the CLAUDE.md discipline brief; VIBE-112/113/115/117
> cover *upstream auto-filing* of downstream defects (a different, outbound triage
> inbox). This document is the **inbound board-quality triage** layer.

---

## Why this exists

The board is an **agent execution queue**. At authoring time it holds **176 active
issues** that a small number of humans (often one) must keep trustworthy enough to
point agents at without re-reading every ticket. Triage is the gate that keeps the
queue legible at that volume: it decides what is genuinely `agent-ready`, what must
drop to `needs-scoping`, what context a ticket is missing, and which hygiene
failures recur often enough to become a standing rule.

Two non-negotiables, inherited from the project guardrails:

- **Linear is the primary source of truth.** Do not assume missing context lives
  elsewhere. If a ticket doesn't carry what an agent needs, the ticket is
  incomplete — say so, don't paper over it.
- **Non-destructive by default.** Triage proposes; humans (or explicit
  high-confidence rules) dispose. Never strip a promise-bearing label or rewrite a
  decision on low confidence. Advisory beats wrong.

---

## The board as it actually is (audit baseline, 2026-05-30)

Measured directly from the Linear GraphQL API across all 176 active VIBE issues
(non-Done, non-Cancelled). This is the empirical baseline triage operates against;
re-run the audit (see *Automations*, below) to refresh it.

**Workflow state:** 150 Backlog · 22 Todo · 3 In Progress · 1 Triage.

**Projects:** Future Improvements (113) · Packaged Vibe (55) · Pre-Build (7) · none (1).

**Label surface (active issues):**

| Label | Count | | Label | Count |
|---|---:|---|---|---:|
| `agent-ready` | 82 | | `blocked-by-external-setup` | 9 |
| `needs-scoping` | 39 | | `observability` | 9 |
| `documentation` | 38 | | `gate` | 6 |
| `critical-path` | 24 | | `wall` | 6 |
| `integration` | 16 | | `backend` | 5 |
| `architecture` | 15 | | `linear-integration` | 4 |
| `infra` | 11 | | `drift-detection` | 3 |
| `chore` | 10 | | `Bug` / `test` / `evals` | 1 each |
| `HUMAN ‼️` | 9 | | | |

**Dependency graph:** dense and mostly healthy — 254 `blocks` edges and ~290 inverse
(blocked-by) views across the active set. Every `agent-ready` ticket carries at
least one relation (zero floating agent-ready tickets).

**What's healthy:**

- **No label contradictions.** Zero tickets carry both `agent-ready` and
  `needs-scoping`.
- **External work is correctly fenced.** All 9 `HUMAN ‼️` tickets (VIBE-165–173)
  are also `blocked-by-external-setup` — the pairing the rubric asks for.
- **Acceptance criteria are universal.** 82/82 `agent-ready` tickets state
  acceptance criteria.

**What needs hardening (the trust gap):**

1. **Gate convention is split, and one half is mislabelled.** There are 25
   gate-shaped tickets under two conventions:
   - 6 in **Packaged Vibe**, titled `[Gate] …`, correctly carrying the `gate`
     label and correctly *not* `agent-ready`.
   - 19 in **Future Improvements**, titled `GATE: …`, carrying `agent-ready` but
     **missing the `gate` label entirely** (VIBE-7, 11, 16, 20, 26, 29, 32, 35,
     39, 44, 51, 57, 61, 65, 69, 73, 77, 82, 94). The board can't be filtered for
     "all gates," and these read as ordinary build work.
2. **Under-specified gates.** The 6 `[Gate]` bodies are ~365–400 chars and state a
   goal without a concrete validation matrix (VIBE-89 is the longest at ~1.2k and
   still lists a definition-of-done, not a pass/fail matrix). Per the rubric, *a
   gate is `agent-ready` only if it spells out the matrix* — these are not yet
   `agent-ready`, which is correct, but they will block their milestones from
   closing cleanly until the matrix exists.
3. **`agent-ready` structural completeness varies.** All have acceptance criteria,
   but machine-detectable presence of the rubric's canonical sections is uneven
   across the 82: Implementation plan ~67%, Source link ~43%, Suggested validation
   / Agent-handoff / Agent-execution-target each ~38%, Cross-repo notes ~22%. Not
   every ticket needs every section, but a `GATE:` validation ticket with no
   concrete runbook (e.g. VIBE-7 lists criteria but no pass/fail matrix) is the
   recurring miss.

Items 1–2 are remediated in the VIBE-177 PR (see *Remediation executed*). Item 3 is
advisory — it drives the per-class minimums and the CLAUDE.md feedback loop below.

---

## 1. Triage taxonomy — the classes of VIBE work

Every VIBE ticket is one of these classes. The class determines the **minimum
context** triage requires before the ticket can be trusted at its claimed label.

| Class | What it is | Lives in | Minimum required context |
|---|---|---|---|
| **Platform-pattern extraction** | Behavior-preserving port/template of a `bin/*` capability for downstream reuse | Future Improvements | Target sentence · which seam/module · acceptance criteria · validation (usually `bin/ci-local` + module-isolation) · `blocked-by` its milestone's contract ticket |
| **Packaging / productization** | Building Packaged Vibe (package surface, distribution, DX) | Packaged Vibe | Same as above **plus** a `blocked-by` edge to the milestone **wall**; consumer tickets blocked on the one foundation ticket |
| **Wall (contract lock)** | Decision checkpoint locked *before* downstream work | any milestone | Locked-decisions list · out-of-scope list · the tickets it guards wired as blocked-by |
| **Gate (validation)** | End-to-end validation checkpoint *after* a milestone | any milestone | A concrete **validation matrix** (checks × env/repo shapes × pass/fail) · blocked-by the milestone's leaf tickets |
| **Scoping** | A decision a human/scoping pass must make | any | `needs-scoping` note · required decision outputs · open questions · which ticket/pass answers them |
| **External-setup / HUMAN** | Needs a human + external account/secret | any | `HUMAN ‼️` + `blocked-by-external-setup` · the exact manual steps · what unblocks downstream |
| **Drift / instruction hygiene** | CLAUDE.md-sync, drift-detection, instruction-model | Future Improvements | What drifted · the canonical source · the sync expectation |
| **Incoming** | New issue sitting in **Triage** state (bug report, DX papercut) | Triage | Repro / failing command · affected surface · priority (not a scoping label yet) |

The first question triage asks is *"which class is this?"* — the class picks the
checklist. Misclassification (a gate treated as build work; a contract-dependent
consumer treated as a standalone feature) is the root cause of most false
`agent-ready` labels.

---

## 2. The intelligence contract (inputs → outputs)

Triage Intelligence is a function from **Linear-native signal** to **disciplined,
auditable recommendations**. Prefer explicit heuristics over vague judgement: every
output should trace to a named input and a stated rule.

### Inputs (all read from Linear)

- **Title** — class hint (`GATE:`/`[Gate]`/`[Wall]`/`[HUMAN]` prefixes).
- **Description quality** — presence of the class's required sections; checkable vs
  aspirational acceptance criteria; decided vs listed forks.
- **Labels** — current label set and contradictions.
- **Project / milestone placement** — routes the class and the expected structure.
- **Dependency shape** — `blocks` / blocked-by edges; whether a consumed contract
  is wired (foundation-first) or hidden (false `agent-ready`).
- **Related docs & reference issues** — linked Linear Docs, source PRs, cross-repo
  refs (`DEAL-*` / `LIFT-*` / `PROMPT-*`).
- **Ambiguity signals** — "TBD", "decide", "options:", "we should figure out",
  multiple architectures named without a decision.

### Outputs (each carries a confidence + a reason)

- **Recommended label changes** — with the specific rule that fired.
- **Recommended status changes** — e.g. incoming → keep in Triage until priority set.
- **Missing questions** — the open design forks an agent would otherwise have to
  invent answers to.
- **Suggested description enrichments** — the named sections the class requires.
- **Suggested CLAUDE.md rule updates** — only when a failure *recurs* (see §4).
- **Confidence / escalation** — high-confidence additive fixes may auto-apply;
  anything that removes a promise-bearing label or rewrites a decision stays
  advisory and escalates to a human.

### The decision the contract is built to make: `agent-ready` vs `needs-scoping`

This is the load-bearing call. It is about **design certainty, not
unblocked-ness** — a ticket can be `agent-ready` and still blocked by three others.

Recommend **`agent-ready`** only when *all* hold (full bar in the
[rubric](agent-ready-rubric.md)):

1. Unambiguous one-sentence target.
2. Implementation plan an agent won't have to reverse-engineer.
3. Checkable acceptance criteria (a test/command/file, not "works well").
4. A stated validation/test expectation (`bin/ci-local`, a smoke matrix, fixtures).
5. **No unresolved design decision** left to the agent.
6. **All real dependencies wired** as `blocked-by` — *including foundational
   contracts* (config model, CLI framework, schema). A hidden dependency is the #1
   false-`agent-ready` signal.
7. Context reachable, not assumed (source links, strongest cross-repo refs, Doc).

Demote to **`needs-scoping`** the moment any of: the ticket depends on a
contract/format that doesn't exist yet and isn't pinned upstream; acceptance
criteria are aspirational; the body lists choices without deciding them; it's a
thin stub for non-trivial work; or "done" hides a human/external step. **When you
demote, enrich** — write the open questions, name the ticket/pass that answers
them, wire the edge. Default ambiguous calls to `needs-scoping`; the cost of a
false `agent-ready` (a wasted agent loop shipping the wrong thing) is far higher
than a false `needs-scoping` (a human glance).

---

## 3. Operational workflow

Three trigger modes, increasing in scope:

- **Incoming (continuous).** New issues land in the **Triage** state. Linear's
  Triage Intelligence suggests project/label/assignee/duplicate/related; a human
  accepts or edits. Do **not** auto-stamp `agent-ready`/`needs-scoping` on intake —
  classify, route, set priority, then let the scoping check run.
- **Command-triggered (on demand).** A `bin/vibe triage` pass (proposed below) runs
  the audit heuristics over a ticket, a project, or the whole board and emits a
  report. Use before pulling a ticket, or before declaring a milestone
  agent-ready.
- **Scheduled (periodic).** A weekly board sweep re-runs the audit, diffs against
  the last baseline, and surfaces *new* hygiene failures (a freshly-mislabelled
  gate, a consumer ticket that lost its edge) plus CLAUDE.md-rule candidates.

**Safe to auto-apply** (additive, reversible, high-confidence): add `gate`/`wall`
from a title prefix; add a `related` link Linear is confident about; add a missing
`blocked-by-external-setup` to a `HUMAN ‼️` ticket; suggest (not apply) enrichment
text.

**Stays advisory** (promise-bearing or lossy): adding or removing
`agent-ready`/`needs-scoping`; changing priority; rewriting acceptance criteria;
closing/merging as duplicate; any low-confidence call.

**Reviewer validation.** A triage recommendation is validated the same way a PR is:
does the cited rule actually fire on the cited input? Spot-check that a
recommended `agent-ready` ticket clears all seven bars, and that a recommended
demotion names its open questions. The audit is reproducible from the API, so any
recommendation can be re-derived rather than trusted.

---

## 4. The CLAUDE.md feedback loop

Triage is not only per-ticket; it watches for **patterns**. When the same hygiene
failure shows up across many tickets, that is a signal the *standing instructions*
are missing a rule — fix it once in CLAUDE.md (or the rubric) instead of N times on
the board.

Promotion bar: a failure becomes a candidate CLAUDE.md/rubric rule when it (a)
recurs across **≥3 tickets or ≥2 sweeps**, (b) is stateable as a checkable rule, and
(c) isn't already covered. Triage proposes the rule as a PR (honoring the
**Sync rule** — `.coderabbit.yaml` updated in the same PR); a human approves.

The failure → rule mapping this audit already supports:

| Recurring failure | Rule it should produce |
|---|---|
| Gate tickets titled but not `gate`-labelled | *Ticket-structure rule:* gate/wall tickets MUST carry the matching label; CI/triage adds it from the title prefix. |
| `GATE:`/`[Gate]` tickets with no pass/fail matrix | *Acceptance-criteria rule:* a gate is `agent-ready` only with a concrete validation matrix (checks × env shapes × pass/fail). |
| Consumer ticket missing edge to its contract | *Module-boundary rule:* one foundation ticket, many thin consumers blocked on it; never N copies that each "invent the framework." |
| `agent-ready` with no validation section | *Local-validation rule:* every `agent-ready` ticket names how it's proven (`bin/ci-local` / smoke matrix / fixtures). |
| Aspirational acceptance criteria | *Safe-execution rule:* "works well" is not a criterion; each must be agent-verifiable. |

---

## 5. Linear Triage Intelligence configuration

Linear's **Triage Intelligence** (team → Triage settings) is the inbound surface.
Two things to configure: the **Guidance** free-text field and the per-suggestion
**Behavior** rules. The Guidance field is not exposed in Linear's public GraphQL
API (only `triageEnabled` / `productIntelligenceScope` are), so it is set in the UI
— **this document is its canonical source**; paste from here and keep them in sync.

### 5a. Guidance text (paste verbatim into "Optional agent guidance")

```
VIBE's board is an AGENT EXECUTION QUEUE. Labels are promises about what happens
when an agent pulls a ticket — keep them trustworthy. Linear is the source of
truth: never assume missing context exists elsewhere.

ROUTING (project):
- "extract / template / port a bin/* capability for downstream reuse" -> Future Improvements
- "Packaged Vibe", packaging, distribution, the published `vibe` package, PR-autopilot productization -> Packaged Vibe
- pre-build analysis / strategy / ADRs -> Pre-Build

LABELS — suggest, do not auto-apply the scoping pair:
- agent-ready = NO open design decision is left to the agent (it may still be
  blocked). Requires: 1-sentence target, implementation plan, CHECKABLE acceptance
  criteria, a stated validation method, all real dependencies wired as blocked-by
  (including foundational contracts), and reachable context. Only suggest it when
  ALL hold.
- needs-scoping = a decision must be made first (a fork is open, a contract doesn't
  exist yet, criteria are aspirational, or it's a thin stub). DEFAULT here when
  unsure — a wrong agent-ready is far costlier than a wrong needs-scoping.
- Never suggest both agent-ready and needs-scoping on the same ticket.
- gate = end-to-end validation checkpoint AFTER a milestone (title "GATE:" / "[Gate]").
- wall = contract-lock checkpoint BEFORE downstream work (title "[Wall]").
- HUMAN ‼️ work needing a human/external account -> also add blocked-by-external-setup.

INCOMING ISSUES (bug reports, DX papercuts): keep in Triage, suggest type labels
(Bug/infra/integration/etc.) and a priority — do NOT stamp agent-ready/needs-scoping
on intake. Priority is a FIELD (Urgent/High/Medium/Low), never a P0-P3 label.

DEDUPE/RELATED: prefer linking related issues over filing duplicates; surface likely
duplicates rather than merging. Wire genuine contract dependencies as blocked-by.

CONFIDENCE: additive, reversible suggestions (add a missing structural label, link a
related issue) are safe. Anything that removes a label, changes priority, rewrites a
decision, or is low-confidence stays advisory for a human. See
docs/review/triage-intelligence.md and docs/review/agent-ready-rubric.md.
```

### 5b. Behavior rule recommendations

| Suggestion | Recommended | Why |
|---|---|---|
| **Assignee** | **Show** | Effectively solo team; auto-assign adds little. Keep advisory; revisit if the team grows. |
| **Project** | **Show now → Auto-apply later** | Routing into Future Improvements / Packaged Vibe / Pre-Build is high-value and rule-driven; promote to Auto-apply once suggestions prove reliable. |
| **Label** | **Show (never Auto-apply)** | Labels are promises. `agent-ready`/`needs-scoping` require the seven-bar rubric check — keep a human in the loop. Structural labels (`gate`/`wall`) are auto-added by the proposed `bin/vibe triage` rule from the title prefix, not by intake suggestion. |
| **Team** | **Show** | Keep the inherited workspace rule ("Lift with Lou" cross-routing). Surfaces mis-filed issues that belong to another team. |
| **Duplicate** | **Show** | High value at 176 issues; keep advisory — never auto-merge (lossy). |
| **Related** | **Show → consider Auto-apply** | Related links are additive and feed dependency hygiene; safe to auto-apply once confident. |

**Sources** stays **Entire workspace** so cross-repo patterns (DEAL/LIFT/PROMPT)
inform suggestions — matching the rubric's cross-repo-evidence emphasis.

---

## 6. Proposed triage automations (to build)

Ordered by value/effort. None are required for the operating model to work; they
make it cheap to run.

1. **`bin/vibe triage` — board-quality audit (advisory).** Wrap the audit
   heuristics used to produce §"audit baseline" into a CLI: fetch the board via the
   Linear GraphQL API and report, per ticket/project/board — label contradictions,
   gate/wall title-vs-label mismatches, `agent-ready` tickets missing a required
   section for their class, gates missing a matrix, and consumer tickets whose
   contract edge is absent. Read-only by default; `--fix` only for the additive,
   reversible class (add `gate`/`wall` from title prefix). *Effort: low — the audit
   already exists as a script.*
2. **Structural-label autofix.** A scheduled (or `--fix`) pass that adds the `gate`
   label to `GATE:`/`[Gate]` titles and `wall` to `[Wall]` titles. Additive, safe.
3. **Gate-matrix linter.** Flag any `gate`-labelled ticket whose body lacks a
   pass/fail matrix; block it from carrying `agent-ready` until the matrix exists.
4. **Weekly sweep → CLAUDE.md-rule candidates.** Scheduled run that diffs against
   the last baseline and, when a failure clears the promotion bar (§4), opens a
   draft PR proposing the CLAUDE.md/rubric rule + the matching `.coderabbit.yaml`
   update.
5. **Incoming enrichment assistant.** For issues in the Triage state, suggest the
   class's missing sections as a comment (advisory) so the reporter can fill them
   before the scoping check runs.

These mirror the **Speed rule**: each tightens the loop (faster to trust a label,
faster to spot drift) without trading away the **non-destructive** guardrail.

---

## 7. Remediation executed in the VIBE-177 PR

High-confidence, additive board fixes applied with this document (see PR
description for the exact API calls and results):

- **Added the `gate` label** to the 19 `GATE:`-titled Future Improvements tickets
  so all 25 gates are filterable under one convention.
- **Flagged the 6 under-specified `[Gate]` Packaged Vibe tickets** with a triage
  note recording that a concrete validation matrix is still required before they
  can gate their milestone (and before they could ever be `agent-ready`).

Everything else (item 3 of the audit, the per-class enrichment backlog) is left
**advisory** — surfaced here and via the proposed `bin/vibe triage` pass, not
mass-applied, per the non-destructive guardrail.

---

## 8. Rollout plan (adopt without noisy churn)

1. **Land this doc + the two high-confidence remediations** (this PR). No mass
   relabeling.
2. **Paste the Guidance text** (§5a) and **set the Behavior rules** (§5b) in
   Linear. Leave everything on **Show** — observe suggestions for one cycle before
   promoting anything to Auto-apply.
3. **Build `bin/vibe triage`** (automation #1) and run it advisory-only for a sweep
   or two. Compare its output to human judgement; tune the heuristics.
4. **Promote the safe automations** (#2 structural-label autofix, Project/Related
   Auto-apply) once their suggestions are trusted.
5. **Turn on the weekly sweep** (#4) and let the CLAUDE.md feedback loop run — but
   keep the promotion bar (§4) so the instruction set grows slowly and only on real,
   recurring failures.

Success is the rubric's success, made continuous: `agent-ready` stays a trustworthy
promise, demotions come with their open questions written out, and the board stays
operable as a high-volume, low-context agent queue.
