# PR Autopilot — drive a PR to merge

> **What this is.** The concrete how-to behind the [`/pr-autopilot`](../../.claude/commands/pr-autopilot.md)
> skill. It is the loop the self-hosted Claude Code runner (VIBE-191/194) runs
> after opening a PR, and is runnable locally. Design spec:
> [`docs/architecture/VIBE-140-cloud-coding-environment.md`](../../docs/architecture/VIBE-140-cloud-coding-environment.md) §5.

The principle: **opening the PR is the *start* of the agent's job, not the end.**
The agent holds the PR open and works it to a terminal state (merged / ready /
escalated) within a wall-clock budget (default **90 minutes**), and it never
auto-merges — the human gate is the trust boundary (ADR-001).

---

## 1. Poll PR + CI + review status

```bash
# CI checks (rollup) for the head branch's PR
gh pr checks <pr> --json name,state,bucket

# PR review + mergeability state
gh pr view <pr> --json mergeable,mergeStateStatus,reviewDecision,statusCheckRollup,isDraft

# CodeRabbit posts as a reviewer/comment bot — detect its review + a rate-limit notice
gh pr view <pr> --json latestReviews,comments \
  --jq '.latestReviews[] , (.comments[] | select(.author.login|test("coderabbit";"i")))'
```

Buckets to act on: `fail`/`pending` CI, `CHANGES_REQUESTED`, `CONFLICTING`
mergeable state, or a CodeRabbit rate-limit message.

## 2. Fix failing CI (scoped)

Reproduce locally over **only** the changed module, then fix and push:

```bash
# map the diff to the pytest targets that matter (single source of truth:
# testscope.py — it reads changed filenames on stdin and prints the targets)
git diff --name-only origin/main...HEAD | PYTHONPATH=. python -m vibe.testscope
bin/ci-local                       # local stays the source of truth
git commit -am "<TICKET>: fix CI (<what>)" && git push
```

Cap fix attempts (default 3). If still red, **escalate** (§5) rather than looping
forever.

## 3. Resolve conflicts by rebase (never merge main in)

```bash
git fetch origin main
git rebase origin/main            # resolve conflicts
bin/ci-local
git push --force-with-lease       # feature branch ONLY — never main
```

Full rules: [`branching-and-rebasing.md`](branching-and-rebasing.md). Standing
rule: **rebase, never merge; force-push feature branches only, never `main`.**

## 4. Work ahead on blockers while waiting

Discover tickets **blocked-by the current ticket** via the Linear GraphQL API
(not `bin/ticket get` — it renders relations as self-references, VIBE-2):

```graphql
query($id: String!) {
  issue(id: $id) {
    identifier
    # tickets that depend on THIS one — candidates to work ahead on
    inverseRelations(filter: { type: { eq: "blocks" } }) {
      nodes {
        relatedIssue {
          identifier
          title
          state { name }
          labels { nodes { name } }
          # are THEIR other blockers cleared?
          relations(filter: { type: { eq: "blocks" } }) {
            nodes { relatedIssue { identifier state { name } } }
          }
        }
      }
    }
  }
}
```

Keep a candidate only if:
- it is labelled **`agent-ready`** (per [`agent-ready-rubric.md`](../../docs/review/agent-ready-rubric.md)),
- all of *its* other blockers are merged/done, and
- you are under the **max in-flight PR cap** (default 3).

Then, for each kept candidate — base is **always `main`**, opened as a **draft**:

```bash
# branch OFF the in-flight work so it builds on the right code...
git switch -c <DEP-TICKET> <current-in-flight-branch>
# ...do the work, validate scoped...
bin/ci-local
git push -u origin <DEP-TICKET>
# ...but the PR TARGETS main, as a draft until the dependency merges:
gh pr create --base main --head <DEP-TICKET> --draft \
  --title "<DEP-TICKET>: <title>" --body-file <neutral-template>
```

Wire the Linear `blocked-by` edge (this dep is blocked by the current ticket).
When the dependency PR merges:

```bash
git switch <DEP-TICKET> && git fetch origin main && git rebase origin/main
bin/ci-local && git push --force-with-lease
gh pr ready <dep-pr>     # flip draft -> ready
```

> **Why never a feature-branch base:** CI triggers only on PRs to `main`. A
> stacked base gets no CI signal and tangles merge order. Build on the branch,
> target `main`.

## 5. Escalate to Slack (and take help back)

Triggers: CodeRabbit rate-limited/unavailable, 90-minute ceiling hit, repeated
unfixable CI/conflict, or anything needing human judgment (secrets,
external-account actions, ambiguous product calls).

Post a **structured** message to `#vibe-agents` under the neutral bot identity:

```json
{
  "ticket": "VIBE-123",
  "pr": "https://github.com/<owner>/<repo>/pull/456",
  "stuck_on": "CodeRabbit returned 429 for 20m; cannot obtain a review",
  "tried": ["re-requested review x3", "waited 20m"],
  "ask": "Re-run CodeRabbit or approve manually?"
}
```

Then **watch the thread**: a human reply is guidance. Parse it, apply it, resume
the loop. (Mechanics land in VIBE-196: Slack events → parse → inject into runner
context.)

## 6. De-attribution (runner only)

For the headless cloud runner (VIBE-197), strip Claude/AI authorship from
everything written to GitHub:

```bash
git config user.name  "<neutral-bot-name>"
git config user.email "<neutral-bot-email>"
# commit via a wrapper/template that omits any Co-Authored-By: Claude trailer
# PR body + comments use neutral templates (no "Generated with Claude Code")
```

A pre-push guard rejects an accidental attribution trailer in runner commits.
**Scope:** runner only — human/local attribution is unchanged.

---

## Terminal states

| State | Meaning |
|---|---|
| **Merged** | The human gate merged it. Done. |
| **Ready, green, approved** | Awaiting the human merge decision. Done for autopilot. |
| **Escalated** | A human has been pinged with actionable context. |
| **Timed out (90m)** | Budget spent — *always* followed by an escalation, never silent. |

## Related

- [`/pr-autopilot`](../../.claude/commands/pr-autopilot.md) — the skill entry point
- [`stacked-vs-milestone-prs.md`](stacked-vs-milestone-prs.md) — when to stack vs. sequence
- [`branching-and-rebasing.md`](branching-and-rebasing.md) — rebase rules
- [`pr-merge-linear.md`](pr-merge-linear.md) / [`pr-opened-linear.md`](pr-opened-linear.md) — Linear ↔ PR sync
