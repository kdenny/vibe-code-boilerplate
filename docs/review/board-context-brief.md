# VIBE Board-Context Brief

> **What this is.** The **substance layer** of the VIBE board: the durable
> project truths, recurring execution hazards, and open contradictions an agent
> needs in its head *before it pulls a ticket*. It is evidence-derived from the
> live board (~198 active VIBE issues, the milestone-plan doc, ADR-001, and the
> repo) — not a style guide and not a cleanup log.
>
> **It sits ABOVE two existing docs and never restates them:**
> - [`agent-ready-rubric.md`](agent-ready-rubric.md) owns what the
>   `agent-ready` / `needs-scoping` / `wall` / `gate` labels *mean* and the 7
>   readiness bars.
> - [`triage-intelligence.md`](triage-intelligence.md) owns the *maintenance
>   system* (taxonomy, the structural audit, label counts, the safe-auto-apply
>   boundary, the board→CLAUDE.md feedback loop).
>
> This brief records *what is true about the work* — the locked decisions and
> the patterns that fool an agent — so neither has to be rediscovered. Read it in
> under five minutes. Source of authorship: VIBE-178.

---

## 1. The board at a glance

VIBE is an **agent execution queue**, not a backlog. A label is a promise about
what happens when an agent pulls the ticket. The board is organized by
**milestones**, and every milestone has the same topology, repeated ~14 times:
a **wall** (scopes + sets acceptance criteria) → parallel **leaf** work tickets →
a **gate** (validates and confirms every wall criterion). See CLAUDE.md "Walls &
gates" for the discipline.

Two projects drive the critical path; almost everything else feeds them:

- **Packaged Vibe** (VIBE-83 line) — turn VIBE into a single private `vibe`
  Python package DEAL can install. **v0 ships ONE capability: PR Autopilot.** The
  four-module taxonomy is *documented future direction, not v0 work.*
- **Cloud Coding Environment / Self-Hosted Runner** (VIBE-140 line) — the remote,
  Slack/Linear-triggered agent that opens PRs into the review firewall and drives
  them to merge. This is the *runtime* that exercises the packaged capability.

Supporting domains: local setup/worktrees/validation; docs & instruction sync
(Claude-first model); extracted platform patterns (the largest slice — Slack,
Neon, Fly, Axiom, GitHub Actions, …, each a leaf+gate milestone); and
triage / upstream-filing / intake.

### Shipped foundation ledger — do not re-derive landed work

These already exist on `main`. Compose with them; a ticket that proposes to build
one from scratch is mis-scoped.

| Artifact | What it is |
|---|---|
| `vibe/testscope.py` | Single source of module-scoped test selection (`INTEGRATION_SEAMS`, "main is the backstop"). Consumed identically by `bin/ci-local --scope`, `tests.yml`, and the cloud QA path. |
| `bin/ci-local` (`--scope`, `--fast`) | One-command local validation; the source of truth (CI mirrors it). |
| `.envrc` + `uv.lock`/`requirements.lock` | direnv activation (`direnv allow`) + pinned, cacheable uv install with pip fallback (VIBE-176/185). |
| `.vibe/.venv` + `.deps_installed` | Worktree Python env + readiness marker, already wired in `bin/vibe` (lines 83-86). |
| `docs/review/agent-ready-rubric.md`, `triage-intelligence.md`, `external-service-milestone-pattern.md` | The label contract, the triage operating model, the external-service milestone shape (+ `.vibe/provider-docs-index.schema.json`, `.vibe/handoff-state.schema.json`). |
| `docs/decisions/ADR-001-cloud-coding-agent-selection.md`, `docs/architecture/VIBE-140-cloud-coding-environment.md` | The binding cloud-agent decision + the cloud program plan. |

---

## 2. Locked decisions / project truths

Settled decisions an agent **must inherit, not re-open**. One line each, with the
citation. (Where a decision lives *only* in Linear/wall prose and not yet in a
repo doc, that placement gap is flagged — it is actionable VIBE-178 substance.)

1. **`vibe` package v0 = PR Autopilot ONLY.** Dist-name = import-namespace =
   `vibe`; private (never PyPI); single package with à-la-carte extras. The
   four-module taxonomy (`linear`/`neon`/`axiom`/`fly`) is documented *future*
   direction, not buildable v0 work. First release `0.1.0`, semver after.
   *(VIBE-83 #1/#2/#3/#8; VIBE-84/88 out-of-scope.)*

2. **Config contract.** The package core works with **no `.vibe/` present**
   (injected typed config); `.vibe/` is an *optional* loader. Owned artifact =
   `.vibe/config.toml` + one `.vibe/<integration>.toml` per integration where
   **file presence = enablement**. Secrets are **never values**, only references
   (`gh:ANTHROPIC_API_KEY`) resolved at runtime; committed files stay diff-safe.
   *(VIBE-83 #5; VIBE-84; VIBE-179.)*

3. **DX thesis — "the agent is the operator"** (a locked design constraint, not
   aspiration). `vibe`'s orchestration must beat Claude calling native tools
   directly *or it shouldn't exist*; slash commands are **thin wrappers** (no
   logic in markdown), real logic lives in the `vibe` CLI; **hard non-goal: do
   not re-skin providers** (no `vibe deploy` over `fly deploy`). *(VIBE-179;
   VIBE-83 #6; VIBE-129.)*

4. **Integration token = the platform's own CLI noun** (Fly.io→`fly` *not*
   `flyio`, Neon→`neon`), and the **same token** is identical across CLI verb,
   flags, `.vibe/<integration>.toml`, the `vibe[<integration>]` extra, import
   path, and slash command; the gate must reject divergent naming.
   **⚠ Placement gap:** this contract lives only in VIBE-119/127 wall prose +
   the milestone plan — **not yet in any `docs/review/` file.** *(VIBE-119/127.)*

5. **Cloud-agent selection is settled by ADR-001:** self-hosted headless Claude
   Code on Fly.io = long-term **primary**, Cursor Cloud = short-term **bridge**;
   Devin and GitHub Copilot rejected. Objective = **highest useful code volume
   per dollar** (useful = merged in ≤1 review cycle). **No auto-merge, ever**;
   branch-scoped token, no force-push to main. **⚠ Confirm:** the ADR file status
   reads `Proposed` while VIBE-140 treats it as binding (see §4). *(ADR-001;
   VIBE-136/140/187/191.)*

6. **The cloud runner reuses VIBE's own spine** (`bin/vibe do`, worktrees,
   `bin/ci-local`, testscope, `/pr` + `/pr-autopilot`) — **not** a parallel
   toolchain. **De-attribution is runner-only** (strip Co-Authored-By / "Generated
   with Claude Code", neutral identity); human/local sessions keep normal
   attribution. The autopilot loop runs to a **terminal state** (merged /
   escalated / timed-out) with a hard **90-minute** ceiling. *(VIBE-191/194/197;
   ADR-001.)*

7. **Local validation contract** (settled, partly shipped). `bin/ci-local` is the
   one-command source of truth (CI mirrors local, not the reverse);
   `testscope.py` is the single module-scoped selector consumed by
   `--scope` / `tests.yml` / cloud QA; `testscope`, `.envrc`, `uv.lock`
   already exist — compose, don't reinvent. *(VIBE-34/186/176/185.)*

8. **Instruction model is Claude-first and co-owned** (CLAUDE.md + skills, no
   single canonical file); CLAUDE.md stays **per-repo**; legacy agent-agnostic
   recipes are **retired** into skills; downstream sync is latest-safe-by-default
   with drift visibility. **⚠ Placement gap + live contradiction:** this lives
   only in VIBE-119 wall / VIBE-180 prose while `agent_instructions/CORE.md:3`
   still calls itself "the single source of truth" and the
   `generate-agent-instructions` CLI still ships (see §4). *(VIBE-119/120/121/180.)*

9. **Upstream-first / no-shim is policy**, enforced by the auto-filing pipeline:
   internal Packaged-Vibe defects file into VIBE **fully automatically** (no human
   approval); external reporters get a coerced-optional GitHub issue + a daily
   Actions→Linear sync; trigger classes and the five triage buckets are
   enumerated and locked. *(VIBE-111/112/113/114.)*

10. **Downstream rollout order is fixed:** DEAL is the **first** PR-Autopilot
    pilot (M2 / `0.1.0` proof); broader module sync goes **LIFT (M3) → PROMPT
    (M4) → DEAL (M5)**, and M5 is deliberately left **unscoped** until LIFT+PROMPT
    learnings exist — do not pre-scope it. M1 and M2 are allowed to overlap.
    *(VIBE-83 #10; milestone plan §3/§4/§5; VIBE-95/133.)*

---

## 3. Recurring ambiguities an agent trips on

Failure **patterns** the board reproduces. When you pull a ticket, watch for
these — each is a real defect class with a canonical exemplar. (These are the
substance behind the rubric's bars; the rubric says *what ready means*, this says
*how readiness is faked in practice*.)

1. **Phantom contracts — verify cited artifacts exist on disk.** A
   `needs-scoping → agent-ready` re-promotion that cites a foundational artifact
   (a doc section, a `.vibe/*.schema.json`, a pattern file) is only honest once
   that artifact **actually exists and its producing ticket is Done.**
   *Exemplar:* the 27 external-service install tickets (VIBE-147–173) were
   re-promoted citing `external-service-milestone-pattern.md` + the handoff/
   provider-docs schemas while VIBE-141 was still In Progress. **Now resolved —
   VIBE-141 merged and all three artifacts are on `main`** — which is exactly why
   the *rule* is load-bearing: the re-promotion was a false promise for the window
   it was un-merged. Check the file before trusting the label.

2. **Matrix-less gates.** A `gate` is not closeable on intent or prose alone — it
   needs a concrete **checks × repo-shape × pass/fail matrix** plus at least one
   end-to-end run on a real shape. *Exemplar:* only ~5 of 19 Future-Improvements
   gates carry a real matrix (VIBE-82 is the template); the rest
   (e.g. VIBE-7/44/51/57/65/94) state only "validate X end to end". The label-
   presence side of this is triage-intel's; the **content gap that 14 still lack
   the matrix after any label fix** is the durable truth here.

3. **Prose-not-edge dependencies.** A contract/schema/scoping dependency MUST be
   a Linear `blocked-by` edge, never English. *Exemplars:* gates that say "stay
   blocked until leaf tickets complete" (VIBE-11/32/35); cloud tickets naming
   "P-fly"/"P-slack" in prose (VIBE-185→190, VIBE-192/196→184); the runner
   PR-autopilot cluster (VIBE-194) with **no edge** to the engine extraction it
   consumes (VIBE-128/129). Corollary: **`agent-ready` may not be blocked-by a
   `needs-scoping` ticket** — if your blocker's design is open, so is yours
   (VIBE-192/196 blocked-by the unscoped VIBE-184).

4. **Unlabeled tickets on an execution queue.** Every ticket carries exactly one
   scoping label at creation; an unlabeled ticket is **untriaged, not implicitly
   ready.** *Exemplar:* VIBE-142–146 (Packaged Vibe) carry no label and are
   1–3-sentence intent stubs that overlap VIBE-131/143 with no `relates-to` edge —
   classify and dedupe before any can be pulled.

5. **Smuggled design forks.** A ticket keeps `agent-ready` while delegating a real
   decision to the agent. *Exemplars:* VIBE-17 ("choose where the contract
   lives… pick the smallest option" — for a contract VIBE-18/19 *consume*);
   VIBE-30 ("either scaffold OR stop copying"); VIBE-9 (undecided opt-out).
   **Where a shared/consumed contract or sync policy lives is a foundation
   decision, not an agent default** — decide upstream or demote.

6. **Softened-decision re-openings.** A downstream ticket paraphrases a wall's
   locked wording in a way that loosens it. *Exemplar:* VIBE-97 says filing is
   "automatic **or near-automatic**," re-opening the VIBE-111/113 lock of "fully
   automatic, no human approval." Use the wall's exact words; a loosening
   paraphrase is a review-blocking defect.

7. **Verbatim duplication of normative text** (the project's own named
   "instruction-surface sprawl" risk). State shared doctrine **once** in a
   canonical home and link. *Exemplars:* the CLI integration-naming criterion
   pasted whole into both VIBE-119 and VIBE-127; CLI doctrine restated across
   `agent_instructions/CLI.md` + `CORE.md` + CLAUDE.md; spend-cap/kill-switch
   prose re-asserted in VIBE-187/190/198. Duplicated normative text is drift.

---

## 4. Known contradictions to resolve

Honest unknowns — flagged, not papered over. Each warrants a scoping decision
before the affected tickets are safe to pull.

- **Instruction-source precedence is unrecorded.** Four surfaces each imply
  canonicity: the CLAUDE.md banner ("hand-authored… do not regenerate"),
  `agent_instructions/CORE.md:3` ("the single source of truth"), the still-shipping
  `vibe generate-agent-instructions` CLI (`vibe/cli/main.py:1358`), and
  `triage-intelligence.md`. An agent can't tell which wins, and CORE.md also
  ships a **stale generic label scheme** (type/risk/area, P0–P3) that contradicts
  the live VIBE scheme (scoping labels; priority is a field). *Needed:* an explicit
  precedence order in CLAUDE.md + freeze `agent_instructions/` and the generator
  for the revamp.

- **ADR-001 status vs. usage.** The file status reads `Proposed`
  (`docs/decisions/ADR-001-…md`) while VIBE-140 and every VIBE-184–198 footer
  treat it as the binding, unblocking decision. *Needed:* flip the ADR to
  Accepted (or record why it stays Proposed-but-binding).

- **`agent_instructions/` retired vs. live.** VIBE-180 (Done) and the VIBE-119
  wall declare it "being retired," while `agent-ready` VIBE-30 invests in keeping
  the generator regenerable downstream. Two active tickets point opposite
  directions on the same files, and the retirement status lives only in ticket
  prose. *Needed:* a `needs-scoping` decision on the actual lifecycle.

---

## 5. What triage intelligence should inherit

The durable facts future triage automation should be handed so it doesn't
re-survey the board each run (these feed, not duplicate, `triage-intelligence.md`):

- The **§2 locked decisions** as inheritance facts — a ticket that contradicts one
  (builds the four-module taxonomy for v0, assumes a downstream `.vibe/`, re-skins
  a provider, re-opens M5 scope) is mis-scoped regardless of its label.
- The **§1 shipped-foundation ledger** — proposals to rebuild landed work are
  mis-scoped.
- The **§3 failure patterns as detectors**, in particular two checks the current
  baseline lacks: (a) **body-vs-label coherence** (a body announcing a class
  change the label never received) and (b) **cited-artifact existence** (a
  re-promotion citing a file not on disk / a not-Done producing ticket).
- The **§4 contradictions** as standing "do not trust the label until resolved"
  flags on the affected clusters.

---

## 6. Suggested follow-on issues

Discipline gaps this synthesis surfaced that need their own tickets (derived from
the audit follow-ups; not filed by this PR):

| Suggested ticket | Class | Why |
|---|---|---|
| Add concrete validation matrices to the ~14 matrix-less Future-Improvements gates | `agent-ready` | VIBE-82 is the template; the other gates can't validate their milestone without it (§3.2). |
| Classify + dedupe the unlabeled PR-Autopilot stubs VIBE-142–146 | `needs-scoping` | No label, overlapping VIBE-131/143, no edges — untriaged on an execution queue (§3.4). |
| Record instruction-source precedence + freeze status in CLAUDE.md | `agent-ready` | Resolves the four-surface "which wins" contradiction; guard `generate-agent-instructions` from clobbering CLAUDE.md (§4). |
| Durably capture the integration-naming contract in `docs/review/` | `agent-ready` | The §2.4 contract is locked but lives only in wall prose; every integration-skill milestone depends on it. |
| Resolve `agent_instructions/` retired-vs-live (VIBE-30 ↔ VIBE-119/180) | `needs-scoping` | Genuine open lifecycle fork on the same files (§4). |
| Add a body-vs-label coherence check to `bin/vibe triage` | `agent-ready` | The current contradiction check only sees both-labels-present; it misses announced-but-unapplied class changes (§5). |

---

*Provenance: synthesized from a board-wide fan-out over ~198 active VIBE issues,
the milestone-plan doc, ADR-001, and the repo, then verified against `main`
(claims that could not be cited, or that `main` had since resolved, were cut or
re-framed). Keep this brief current as walls lock new decisions — a stale
substance layer is worse than none.*
