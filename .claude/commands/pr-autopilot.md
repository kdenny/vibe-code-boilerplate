---
description: Drive an opened PR all the way to merge — wait for CodeRabbit + CI, fix failures and conflicts, work ahead on blockers, escalate to Slack when stuck
---

# /pr-autopilot — drive a PR to merge (don't stop at "opened")

The default agent loop ends at "PR opened". `/pr-autopilot` is the loop that
**starts** there. It is the behavior the self-hosted Claude Code runner
(VIBE-191/194) executes after every PR it opens, and you can run it locally too.

**Canonical spec:** [`docs/architecture/VIBE-140-cloud-coding-environment.md`](../../docs/architecture/VIBE-140-cloud-coding-environment.md) §5.
**Recipe (the how, with commands):** [`recipes/workflows/pr-autopilot.md`](../../recipes/workflows/pr-autopilot.md).

## Usage

```
/pr-autopilot                 # drive the current branch's PR to merge
/pr-autopilot --pr 123        # drive a specific PR
/pr-autopilot --budget 90m    # override the wall-clock ceiling (default 90m)
/pr-autopilot --no-workahead  # skip picking up blocked tickets while waiting
```

## The core promise

**Do not exit after opening a PR.** Stay alive and drive every PR you opened to a
terminal state — **merged**, **escalated**, or **timed-out-then-escalated** —
within a **90-minute** wall-clock ceiling. Never leave an un-merged PR with no
human notified.

## The loop

Repeat until every tracked PR is merged or the budget is spent:

1. **Poll status** of the PR:
   - CI checks: `tests.yml`, `pr-policy.yml`, `lint.yml`, `security.yml`.
   - CodeRabbit review state (approved / changes-requested / pending / rate-limited).
2. **CI failing** → reproduce locally with **scoped** validation
   (`bin/ci-local` over the changed module via `testscope.py`), fix, commit, push.
   Re-poll.
3. **Merge conflict / behind main** → **rebase onto `origin/main`** (never merge
   `main` in), resolve, **force-push the feature branch only**. See
   [`recipes/workflows/branching-and-rebasing.md`](../../recipes/workflows/branching-and-rebasing.md).
4. **CodeRabbit requested changes** → address each thread, commit, push,
   re-request review. Reply to threads under the neutral identity (see
   De-attribution below).
5. **Everything green + approved** → the PR is ready for the human gate. Do **not**
   merge (no auto-merge). Mark it ready, ping the human if it needs a merge
   decision, and consider it terminal for autopilot purposes.
6. **Work ahead while waiting** (unless `--no-workahead`) → see next section.
7. **Stuck** → escalate to Slack (see Escalation).

## Work ahead on blockers (productive waiting)

While a PR is waiting on review/CI, use the idle time:

1. Query Linear (**GraphQL, not `bin/ticket get`** — relation rendering bug,
   VIBE-2) for tickets **blocked-by the current ticket** plus close same-project
   siblings. Recipe has the exact query.
2. Keep only ones that are genuinely **`agent-ready`** per
   [`docs/review/agent-ready-rubric.md`](../../docs/review/agent-ready-rubric.md)
   — skip `needs-scoping`, uncleared `wall`s, and anything with open design forks.
3. Respect the **max in-flight PR cap** (default 3 — protects the solo reviewer;
   ADR-001's binding constraint). If at the cap, just keep waiting.
4. For a chosen blocked ticket:
   - Branch **off the current in-flight branch** (so it builds on the right code).
   - Do the work; run scoped `bin/ci-local`.
   - Open it as a **DRAFT PR whose base is `main`** — never a non-`main` base.
     CI only runs against `main`; a stacked base gets no signal and tangles merge
     order.
   - Wire the Linear **`blocked-by`** edge to the dependency ticket.
5. When the dependency PR **merges**, rebase the dependent branch onto `main`,
   confirm green, and **flip the draft to ready**.

> **Why draft-to-main and never a feature-branch base:** this is the standing
> repo rule. Dependent work is *built on* the unmerged branch but *targets*
> `main` as a draft until the dependency lands.

## Escalation + human-in-the-loop (Slack)

Escalate to `#vibe-agents` (under the **neutral** bot identity) when:

- **CodeRabbit is rate-limited / unavailable** and you can't get a review;
- the **90-minute ceiling** is hit without a merge;
- CI fails repeatedly (default 3 attempts) in a way you can't fix, or a conflict
  you can't safely resolve;
- you hit **anything needing human judgment** — secrets, external-account
  actions, ambiguous product/UX/branding calls (CLAUDE.md "a human should still
  intervene").

Post a **structured** escalation: ticket, PR link, *what is stuck*, *what you
tried*, and *the specific ask*. Then **watch the thread** — a human reply is
guidance: parse it, apply it, and resume the loop. This is what makes the runner
unattended-by-default but rescuable.

## De-attribution (runner only)

When running as the self-hosted cloud runner (VIBE-197), everything written to
GitHub is neutral:

- commits carry **no** `Co-Authored-By: Claude` trailer;
- PR bodies and GitHub comments carry **no** "Generated with Claude Code" footer;
- the git author and Slack identity are neutral (not "Claude").

**Scope:** this applies to the headless cloud runner only. Local interactive and
human-authored work keep their normal attribution.

## Terminal states

- **Merged** (by the human gate) — success.
- **Ready + green + approved, awaiting human merge** — success for autopilot.
- **Escalated** — a human has been pinged with actionable context.
- **Timed out (90m)** — always followed by an escalation; never silent.
