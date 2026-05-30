# VIBE-140 — Cloud Coding Environment for VIBE: Project Plan

**Ticket (umbrella):** [VIBE-140 — Set up the cloud coding environment for VIBE](https://linear.app/2wrist/issue/VIBE-140/set-up-the-cloud-coding-environment-for-vibe)
**Projects:** [Cloud Coding Environment](https://linear.app/2wrist/project/cloud-coding-environment-92205d9ee9b5) (Phase 1 + foundation) · [Self-Hosted Claude Code Runner](https://linear.app/2wrist/project/self-hosted-claude-code-runner-6d50f3861198) (Phase 2)
**Upstream decision:** [ADR-001 — Cloud Coding Agent Selection](../decisions/ADR-001-cloud-coding-agent-selection.md) (done — Claude Code primary, Cursor fallback)
**Status:** Living plan. Tickets cut (VIBE-184…198). Phase 1 is the short-term bridge; Phase 2 is the long-term primary.

> **SYNC NOTE — this doc and Linear are a matched pair.** The canonical copy of
> this plan lives here in the repo; condensed copies live on the two Linear
> project documents and the VIBE-140 umbrella ticket. **If one moves, move the
> others in the same change.** This mirrors the CLAUDE.md ↔ `.coderabbit.yaml`
> sync rule. When the architecture, the trigger contract, the autopilot
> behavior, or the staged sequence below changes, update this file *and* the
> Linear docs, and note it in the PR.

---

## 0. TL;DR

We are standing up a remote **issue → PR** coding environment for VIBE, decomposed
into two phases so we get value now without betting everything on unproven glue:

1. **Phase 1 — Cursor Cloud (short-term bridge).** Use Cursor Background/Cloud
   Agents — ADR-001's *fallback* engine — as the interim surface to get a remote
   loop running today. Wire **both** entry points (Slack + Linear) for it.
2. **Phase 2 — Self-hosted Claude Code runner (long-term primary).** A headless
   Claude Code runner on a **Fly.io** machine, triggered from **Slack** (with a
   **Linear-trigger spike** behind it), running the **PR-autopilot loop**: it
   does a ticket, opens a PR, and then *does not exit* — it waits for CodeRabbit
   and CI, fixes failures and merge conflicts, **works ahead on blocked tickets**
   while it waits, holds the PR(s) open until merged (**90-minute ceiling**), and
   **escalates to Slack** (with human reply-back) when it gets stuck. Everything
   it writes to GitHub is **de-attributed** — no "written by Claude".

Cross-cutting both phases: **harden the repo for cloud execution** — minimal
cold-start, module-scoped test selection (already seeded by `testscope.py`), and
minimal build/setup time.

The agent never merges. Every path ends at a **reviewable PR into the existing
policy gate** (PR-policy bot + CodeRabbit + human). This is non-negotiable and
matches ADR-001's trust boundary.

---

## 1. Objective & non-goals

**Objective.** Maximize *useful* PRs per dollar (ADR-001's objective function:
merged with ≤1 review iteration) from a remote, unattended-trigger loop that
feeds VIBE's existing Linear/worktree/PR-policy spine.

**Non-goals (this program):**
- **No auto-merge.** Ever. Human-gated merge is the trust boundary (ADR-001).
- **No second source of truth.** Linear stays canonical; the agents feed the
  existing spine, they don't replace `bin/vibe`, `bin/ticket`, or the gate.
- **No big-bang.** Phases and tickets are staged; each lands green and
  independently testable (CLAUDE.md migration posture).

---

## 2. Where we are (and what we already have)

- **Agent selection is decided.** ADR-001 chose **self-hosted/managed Claude Code
  as primary** and **Cursor Background Agents as fallback**, rejecting Devin and
  Copilot on cost-per-useful-PR / source-of-truth grounds. VIBE-140 was blocked
  on that spike; it is now unblocked.
- **The repo is already module-scoped-test-capable.** `vibe/testscope.py`
  (VIBE-137) + `tests/integration/` + `INTEGRATION_SEAMS` (VIBE-174) already let
  us run *only* the suites a change touches. Phase-0 hardening **builds on this**,
  it does not reinvent it.
- **Fast local env exists.** A committed `.envrc` (VIBE-176) makes env setup one
  `direnv allow`. The cloud bootstrap reuses it.
- **`bin/ci-local` is the single validation contract.** The runner uses it; we
  keep it fast.

**Why Cursor first if Claude is the primary?** Time-to-value. Cursor is a managed
surface we can point at the repo in hours; the self-hosted Claude runner is real
infra (Fly machine, trigger ingress, autopilot loop). Running Cursor as the
bridge de-risks the program: we learn the trigger/QA/review ergonomics on a
managed engine while building the cheaper-per-PR primary behind it. ADR-001
explicitly keeps Cursor as the sanctioned fallback, so this is not throwaway.

---

## 3. Two-phase rollout

### Phase 1 — Cursor Cloud (short-term bridge)

| Ticket | What | Label posture |
|---|---|---|
| **VIBE-187** | Stand up Cursor Cloud against the VIBE repo (scoped token, secrets, spend cap, kill switch, opens PRs into the gate) | `HUMAN` · `blocked-by-external-setup` |
| **VIBE-188** | Slack entry point → launch a Cursor agent | `needs-scoping` |
| **VIBE-189** | Linear entry point → launch a Cursor agent | `needs-scoping` |

The two entry points are `needs-scoping` on purpose: the **programmatic launch
API for a Cursor Background Agent is unproven**. We do not pretend it's
agent-ready; the tickets carry the open questions and the decision outputs the
scoping pass must produce.

### Foundation / repo hardening (shared by both phases)

| Ticket | What | Label posture |
|---|---|---|
| **VIBE-184** | Create the VIBE cloud-agents Slack app (bot user, tokens, `#vibe-agents`) | `HUMAN` · `blocked-by-external-setup` |
| **VIBE-185** | Cloud-fast repo bootstrap — minimize cold-start install/build time | `agent-ready` |
| **VIBE-186** | Wire `testscope.py` module-scoped selection into the cloud QA path | `agent-ready` |

### Phase 2 — Self-hosted Claude Code runner (long-term primary)

| Ticket | What | Label posture |
|---|---|---|
| **VIBE-190** | Provision a Fly.io machine for the runner (volume, secrets, kill switch) | `HUMAN` · `blocked-by-external-setup` |
| **VIBE-191** | Self-hosted headless Claude Code issue-to-PR runner on Fly.io | `agent-ready` |
| **VIBE-192** | Slack trigger + progress thread | `agent-ready` |
| **VIBE-193** | **SPIKE** — Linear entry point (blocked by the Slack trigger) | `needs-scoping` |
| **VIBE-194** | PR Autopilot loop (wait for CodeRabbit + CI, fix conflicts/CI, hold ≤90 min) | `agent-ready` |
| **VIBE-195** | Work-ahead on blockers (stacked branches → draft PRs to `main`) | `agent-ready` |
| **VIBE-196** | Slack escalation + human-in-the-loop reply-back | `agent-ready` |
| **VIBE-197** | De-attribution (strip Claude authorship; stealthy re: CodeRabbit) | `agent-ready` |
| **VIBE-198** | Observability, spend tracking & kill switches | `agent-ready` |

---

## 4. Architecture

Same shape for both engines; only the **execution** box differs.

```
 Trigger                 Ingress / Orchestration        Execution                    Gate
 ───────                 ───────────────────────        ─────────                    ────
 Slack  /vibe do X  ─┐                                  Phase 1: Cursor Cloud agent  PR opened on a
  (VIBE-188/192)     ├─►  Slack app (VIBE-184)   ─────► Phase 2: headless Claude     feature branch,
 Linear assign/label ┤    verify, authz, dispatch        Code on Fly.io (VIBE-190/1) base = main
  (VIBE-189/193)     │           │                              │                          │
 (GitHub @mention)  ─┘    reads ticket, runs            bin/vibe do → worktree,            ▼
                          bin/vibe do, picks engine     bin/ci-local (scoped), opens  PR-policy bot
                                                        PR via /pr                    + CodeRabbit
                                                              │                       + human review
                                              PR-autopilot loop (VIBE-194):                │
                                              wait CodeRabbit+CI, fix CI,                   ▼
                                              fix conflicts (rebase main),            Human merge
                                              work-ahead on blockers (VIBE-195),      (NO auto-merge)
                                              escalate to Slack (VIBE-196),
                                              hold open ≤90 min until merged
```

**Invariants (both engines):**
- **One ticket = one branch = one PR**, base = `main`, matching existing VIBE rules.
- **Secrets** live in the engine's secret store (Cursor store / `fly secrets` /
  CI secrets) — never in code, never echoed to logs.
- **Branch-only token.** No force-push to `main`, no merge rights.
- **The agent stops at "PR merged or escalated."** Merge is human-gated.

### 4.1 Entry points (the trigger ingress)

Both phases share **one Slack app** (VIBE-184) and, ideally, one ingress that
routes a normalized `{ticket, engine}` job to the right backend. Slack is the
known-good first surface for both engines; **Linear is the stretch**, which is
why the Linear-side tickets (VIBE-189 Cursor, VIBE-193 Claude-spike) are
`needs-scoping` and the Claude Linear path is explicitly **blocked by the Slack
trigger** (VIBE-192) — we prove the dispatch on Slack, then try to reuse it for
Linear.

### 4.2 Fly.io topology (Phase 2)

- A Fly app (e.g. `vibe-claude-runner`) with a machine sized for one Claude Code
  session + `bin/ci-local`.
- A **persistent volume** holding the cloned repo + dependency cache — this is
  what makes warm runs cheap (feeds VIBE-185's warm/cold contract).
- Secrets via `fly secrets`. **Kill switch** = `fly scale count 0` / `fly machine
  stop`, documented in VIBE-198.

---

## 5. The PR-Autopilot loop (the core Phase-2 behavior)

This is the heart of the program and the thing that makes the runner *useful*
rather than a fire-and-forget PR opener. Specified as the `/pr-autopilot` skill
in this repo (`.claude/commands/pr-autopilot.md`, recipe at
`recipes/workflows/pr-autopilot.md`) and wired into the runner by VIBE-194.

**The runner does not shut down after opening a PR.** It enters the loop:

1. **Wait for review + CI.** Poll the PR's checks (`tests.yml`, `pr-policy.yml`,
   `lint.yml`, `security.yml`) and CodeRabbit's review status.
2. **Fix failing CI.** Reproduce locally with *scoped* `bin/ci-local` (VIBE-186),
   fix, push.
3. **Resolve merge conflicts** by **rebasing onto latest `main`** (never merge
   `main` in) and **force-pushing the feature branch only** — matching the
   standing repo rule.
4. **Address CodeRabbit "request changes"** thread by thread; push; re-request.
5. **Work ahead while waiting** (VIBE-195): find tickets **blocked-by** the
   current ticket (and close siblings) that are genuinely `agent-ready`, start
   them on a branch **based off the in-flight work**, and open them as **draft
   PRs targeting `main`** if the dependency PR hasn't merged. Wire the Linear
   `blocked-by` edge; when the dependency merges, rebase onto `main` and flip the
   draft to ready. Respect a **max in-flight PR cap** (don't out-produce the
   solo reviewer — ADR-001's binding constraint).
6. **Hold open until merged, with a 90-minute ceiling.** The loop runs until
   every PR it opened is merged or 90 minutes elapse. On timeout it **escalates**
   (next), it does not abandon silently.

### 5.1 Escalation + human-in-the-loop (VIBE-196)

Escalate to `#vibe-agents` (under the neutral identity) when:
- **CodeRabbit is rate-limited / unavailable** and the loop can't get a review;
- the **90-minute ceiling** is hit without a merge;
- CI fails repeatedly in a way it can't fix, or a conflict it can't safely resolve;
- it hits **anything needing human judgment** — secrets, external-account
  actions, ambiguous product/UX calls (CLAUDE.md "a human should still intervene").

The escalation is structured (ticket, PR, what's stuck, what it tried, the
specific ask). **The human replies in the Slack thread**, and the runner consumes
that reply as guidance and resumes. This two-way channel is what keeps the loop
unattended-by-default but rescuable.

### 5.2 Why "draft PRs to main" and never a non-main base

CI here only triggers on PRs to `main`. A stacked PR against a feature branch
gets **no CI signal** and tangles merge order. So even when the dependent work
must be *built on* unmerged code, the PR's **base is always `main`**, opened as a
**draft** until the dependency merges. This is the same reasoning behind the
standing repo rule and is baked into VIBE-195.

---

## 6. Repo hardening for cloud execution

The cloud-agent loop is only as cheap as the repo's startup + validation cost.
Three principles, mapped to concrete work:

1. **Minimal startup time to run** → **VIBE-185.** Pin + cache deps, reuse the
   committed `.envrc`, restore the dependency cache from the Fly volume; record a
   cold/warm `bin/ci-local` budget and beat it.
2. **Run only the touched module's code/tests** → **VIBE-186.** Use
   `testscope.py` to map a diff → the exact unit suites + composed seams; full-
   tree CI only for cross-cutting/contract changes. Single source of truth in
   `testscope.py` (no duplicated selection in `tests.yml` vs the cloud path).
3. **Minimal build/setup time** → folded into VIBE-185: trim redundant work in
   `bin/ci-local`, short-circuit when nothing in scope changed, keep the bootstrap
   one-command.

The **speed rule** (CLAUDE.md standing rule #2) applies throughout: if any
hardening step reveals a faster path, surface it.

---

## 7. Trust, secrets, spend & kill switches

- **Agent → repo:** branch-scoped token, branch-only write, no force-push to
  `main`, no merge.
- **Agent → secrets:** read from the engine secret store only; `gitleaks`/secret
  scan still runs in CI; nothing echoed to logs.
- **Agent → merge:** **none.** Human-gated for every path.
- **Spend:** hard monthly cap + alerting on both engines (ADR-001 flags Cursor
  MAX +20% spiky billing and encodes per-useful-PR cost as a rollback trigger);
  per-run + aggregate tracking via VIBE-198 (reusing `bin/costs`).
- **Kill switch:** documented + tested for both engines (Cursor: disable/halt;
  Fly: `fly scale count 0`). The Cursor (Phase-1) controls — branch-only token,
  secret store, spend cap, kill switch, and the Linear agent-guidance blocks —
  are operationalized in
  [`docs/operations/cursor-cloud-agents-runbook.md`](../operations/cursor-cloud-agents-runbook.md)
  (VIBE-187).
- **Reviewer overload is the binding constraint** (ADR-001): a max in-flight PR
  cap protects the solo reviewer. More PRs than one human can review is negative
  value — VIBE-195 enforces the cap.

---

## 8. De-attribution / stealth (VIBE-197)

Everything the **self-hosted runner** writes to GitHub is neutral:
- commits carry **no** `Co-Authored-By: Claude` trailer;
- PR bodies + GitHub comments carry **no** "Generated with Claude Code" footer;
- the git author identity and the Slack bot identity are neutral (not "Claude").

A pre-push guard on the runner rejects an accidental attribution trailer.

**Scope:** runner-only. Human developers and local interactive Claude Code
sessions keep their normal attribution — this is a property of the headless cloud
path, not a repo-wide change.

---

## 9. Dependency graph & critical path

```
Phase 1 (bridge):           ADR-001(done) ─► VIBE-187 ─► VIBE-188 (needs Slack app VIBE-184)
                                                   └────► VIBE-189
Foundation:                 VIBE-185, VIBE-186  (independent, parallel) ; VIBE-184 (Slack app)

Phase 2 (primary):  VIBE-190 ─► VIBE-191 ─┬─► VIBE-194 ─► VIBE-195
                                          │        └─────► VIBE-196 ◄─ VIBE-192
                                          ├─► VIBE-192 ─► VIBE-193 (spike)
                                          ├─► VIBE-197
                                          └─► VIBE-198
                    VIBE-184 ─► VIBE-192
```

- **Genuinely parallel** (`parallelization`): VIBE-185 / VIBE-186 (foundation);
  VIBE-197 / VIBE-198 (after the runner exists).
- **Human/external handoffs** (`blocked-by-external-setup` + `HUMAN`): VIBE-184,
  VIBE-187, VIBE-190 — these gate the agent-ready work behind them.
- **Spikes** (`needs-scoping`): VIBE-188, VIBE-189, VIBE-193 — trigger-API
  uncertainty, written up with the open questions.

---

## 10. Open questions / spikes

1. **Cursor launch API** (VIBE-188/189): is there a supported programmatic way to
   start a Background Agent from an external trigger? If not, what's the path?
2. **Linear → runner** (VIBE-193): cleanest trigger event (assignment / label /
   comment), webhook reachability to Fly, idempotency.
3. **Headless Claude Code on Fly** (VIBE-191): confirm `claude -p` headless runs
   cleanly in the Fly machine with the repo conventions and the branch-scoped
   token; settle the dispatcher home (`vibe/cloud/` vs `bin/`).
4. **CodeRabbit rate limits** (VIBE-196): real-world limits that drive the
   escalation threshold.

---

## 11. Risks

- **Platform maturity** — managed Remote Tasks / Fly runner are young; Cursor
  bridge de-risks by giving us a working loop while we harden Phase 2.
- **Cost runaway** — metered engines spike; hard caps + alerts before enabling
  (VIBE-198), and the ADR-001 rollback triggers stay live.
- **Reviewer overload** — the real ceiling at ~20 PRs/week is *review* bandwidth,
  not dollars; the in-flight cap (VIBE-195) is the mitigation.
- **Stealth vs. honesty of validation** — de-attribution (VIBE-197) is a
  runner-only GitHub-surface choice; it must not weaken CI/secret scanning, which
  still run on every PR.

---

## Related

- [ADR-001 — Cloud Coding Agent Selection](../decisions/ADR-001-cloud-coding-agent-selection.md)
- [VIBE-174 — Modular restructure plan](VIBE-174-modular-restructure-plan.md) (the `testscope.py` / seam layer this builds on)
- [Agent-ready rubric](../review/agent-ready-rubric.md) (the label contract these tickets follow)
- `.claude/commands/pr-autopilot.md` + `recipes/workflows/pr-autopilot.md` (the autopilot skill)
