# ADR-001: Cloud Coding Agent Selection for VIBE

## Status

Proposed

## Date

2026-05-30

## Context

VIBE-136 asks us to validate the cloud coding-agent choice for VIBE before we
commit downstream architecture (this ADR blocks VIBE-140). The brief is explicit
about the objective function: **highest useful code volume per dollar** for an
issue-to-PR workflow that can be triggered from Linear, GitHub, or Slack and open
PRs remotely without a developer babysitting a laptop.

The evaluation must cover:

- Cursor cloud / background agents
- A self-hosted runner path triggerable from Slack or Linear that opens PRs remotely
- Other viable remote coding-agent options for issue-to-PR workflows
- Cost per **useful** PR, reliability, reviewability, and QA fit
- Trigger support: issue comments, issue assignment, Slack commands

### Forces at play

- **VIBE is already Claude Code-native.** The boilerplate is built around `bin/vibe`,
  `bin/ticket`, Linear, git worktrees, a PR policy bot, and risk/area labels. Whatever
  agent we pick has to feed *that* pipeline, not replace it.
- **Small team, undifferentiated heavy lifting is expensive.** Hours spent babysitting
  agent infrastructure are hours not spent on the product. This cuts toward managed.
- **"Per dollar" is a trap if measured naively.** A $0.50 PR that gets rejected and
  needs two human review cycles is more expensive than a $30 PR that merges first try.
  The denominator is *useful* PRs (merged with ≤1 review iteration), not raw PRs.
- **Reviewability and trust boundaries are first-class.** Unattended merge is still not
  safe in 2026 (silent regressions, secret leakage into logs, unwanted dependencies).
  The agent must produce *reviewable* PRs into a human gate, not merge on its own.

## Decision

**Primary path: Self-hosted / managed Claude Code issue-to-PR runner**
(`anthropics/claude-code-action` on GitHub-hosted runners, with Anthropic's managed
**Remote Tasks** as the zero-ops execution surface), triggered from Linear and Slack,
opening PRs into the existing VIBE policy gate.

**Fallback path: Cursor Background (Cloud) Agents** for burst parallelism and when a
task needs Cursor's stronger autonomous loop on a single hard issue.

**Rejected as primary: Devin** — strongest "PM-to-PR" autonomy story, but loses on the
actual objective function (cost per *useful* PR) for a team that already has a
Claude-native pipeline.

> ⚠️ **Decision input required from the human owner — see "Cost Model" and
> "Rollback / Flip Criteria" below.** The recommendation holds under the stated
> assumptions (team size, PR volume, blended labor rate, glue-maintenance hours).
> Two of those numbers are yours to set, and they can flip primary ↔ fallback.

## Options Considered

### Option 1: Self-hosted / managed Claude Code runner (RECOMMENDED — primary)

`claude-code-action` runs on your own GitHub runner with your Anthropic key; triggers on
`@claude` mentions, issue assignment, or explicit automation prompts, and opens a PR.
As of **2026-03-20**, Anthropic's **Remote Tasks** removes the self-hosting burden: define
a repo + prompt + trigger (schedule / webhook / GitHub event), and it runs on Anthropic's
infra with connectors into Slack, Linear, and Sentry. Claude Code in Slack posts thread
progress and exposes a one-click **Create PR** button.

**Pros:**
- **Cheapest per useful PR.** ~$0.50–$2 (small) to $5–$15 (large) per PR on Sonnet; a
  team doing 10–15 PRs/week lands around $15–$25/month of model spend.
- **Native fit with the existing spine** — Linear, worktrees, PR policy bot, labels. No
  parallel toolchain, no second source of truth.
- **Reviewability is built in:** output is a normal PR into your gate; nothing merges itself.
- **Two execution modes on one model line:** self-hosted Actions (max control) *or*
  managed Remote Tasks (zero ops). You can start managed and in-source later, or vice versa.
- **Trigger coverage is complete:** issue assignment, issue comments, Slack commands.

**Cons:**
- Self-hosted mode means *you* own runner reliability, secrets, queueing, and retries —
  unless you use Remote Tasks (which then re-introduces a managed dependency).
- Autonomy on a *single* very hard issue is slightly behind Cursor's background loop.
- Remote Tasks is young (shipped March 2026); platform maturity risk.

### Option 2: Cursor Background / Cloud Agents (RECOMMENDED — fallback)

Cursor's Background Agent runs the IDE assistant autonomously on a task spec with no human
in the loop. Strong autonomy: **65.7% SWE-bench Verified** on Sonnet 4.6.

**Pros:**
- **Best autonomous single-task loop** of the metered options, at a competitive model tier.
- **Trivial parallelism** — fan out N cloud agents without you managing concurrency.
- Excellent DX if the team already lives in Cursor.

**Cons:**
- **Cloud Agents require MAX mode → +20% surcharge** on every run, and billing is
  token-metered and spiky (a single run on a 50k-line repo can eat ~22.5% of a $20 credit).
  Hard to forecast "per dollar."
- **Weaker native fit** with a Linear-centric, policy-gated GitHub workflow; you bolt the
  trigger/PR glue on yourself.
- Ecosystem lock toward Cursor; reviewability gating is less first-class than a plain PR.

### Option 3: Devin (Cognition) (REJECTED as primary)

The most "assign-it-and-walk-away" autonomous engineer. Usage-billed in ACUs
(~15 min each): Core $20/mo + **$2.25/ACU**; Team $500/mo incl. 250 ACUs @ **$2.00/ACU**.

**Pros:**
- Strongest end-to-end "issue → PR with tests" autonomy and parallel-Devin throughput.
- Good for *volume* of low-stakes, well-specified grunt tasks.

**Cons:**
- **Loses the objective function.** Moderate task = 5–20 ACUs = **$11–$45 per attempt**.
  SWE-bench Verified **51.5%**; production **PR merge rate ~67%** → roughly **1 in 3 PRs
  rejected.** Cost *per useful PR* is therefore ~$16–$67+ once you divide by merge rate.
- Most expensive per unit of accepted work for a team that already has a cheaper, native path.
- Separate toolchain and trust surface to maintain alongside the Claude/Linear spine.

### Option 4: GitHub Copilot Coding Agent (REJECTED — viable runner-up)

Assign a GitHub issue → Copilot opens a PR autonomously; consumes Actions minutes.
Pro $10 / Pro+ $39 / Business $19-user / Enterprise $39-user.

**Pros:**
- Cheapest entry point; **native GitHub issue→PR**; zero infra to run.

**Cons:**
- **Usage-based billing shift on 2026-06-01** (AI Credits + token metering) makes near-term
  cost forecasting unstable.
- **Linear-blind:** triggers off GitHub issues, not Linear. VIBE's source of truth is Linear,
  so we'd be fighting the grain or duplicating issues.
- Less steerable than Claude Code for our conventions (labels, risk policy, worktrees).

## Minimum Viable Architecture (remote issue-to-PR)

```
 Trigger                Orchestration              Execution                 Gate
 ───────                ─────────────              ─────────                 ────
 Linear issue   ─┐
  (assigned /    │      Webhook / GitHub      ┌─ claude-code-action          PR opened on
   commented)    ├────► event filter   ──────►│   on GH runner   ──┐         feature branch
 Slack command  ─┤      (or Remote Tasks      │   (self-hosted)    │         │
  (/vibe do …)   │       managed trigger)     └─ OR Remote Tasks ──┘         ▼
 GitHub @claude ─┘            │                    (managed cloud)      PR Policy bot
                              │                          │              (ticket ref, risk
                     reads ticket + repo,        clones repo, runs       label, branch name)
                     creates worktree/branch,     tests, commits,              │
                     applies VIBE conventions     opens PR                     ▼
                                                                          Human review → merge
                                                                          (NO auto-merge)
```

Key properties:
- **One ticket = one branch = one PR**, matching existing VIBE rules.
- **Secrets** (`ANTHROPIC_API_KEY`, `LINEAR_API_KEY`) live in GitHub Actions / Remote Tasks
  secret stores — never in code, never echoed to logs.
- **The agent stops at "PR opened."** Merge stays human-gated behind the policy bot.
- Start on **managed Remote Tasks** (zero ops) and graduate to **self-hosted Actions** only
  if you need custom build environments or tighter network egress control.

## Cost Model (with assumptions)

**Confirmed inputs (owner, 2026-05-30):**
- Team size: **1 engineer (solo)**
- PR throughput target: **~20 PRs / week ≈ 87 PRs / month**
- Blended cost of a review cycle: **~$100 / hr** *(assumption — solo opportunity cost;
  adjust if your real number differs)*
- "Useful PR" = merged with ≤1 review iteration; model = Claude Sonnet, small-to-medium PRs.

| Option | Raw cost / PR | Merge (useful) rate | **Cost / useful PR** | **Monthly @ ~87 PRs (model spend)** |
|---|---|---|---|---|
| **Claude Code runner** (Sonnet) | $0.50–$15 (≈$2–3 avg) | high (human-gated, steerable) | **≈$3–$5** | **≈$175–$350** |
| **Cursor Background** (MAX +20%) | metered, spiky | 65.7% SWE-bench class | **≈$8–$20** | ≈$700–$1,700+ |
| **Devin** (ACU) | $11–$45 | ~67% merge | **≈$16–$67** | ≈$1,400–$5,800+ |
| **Copilot coding agent** | low base, metering shift 6/1 | moderate | unstable to forecast | $10–$39 + heavy usage |

**Why volume makes the choice starker, not closer:** at 87 PRs/month, model cost scales
linearly while glue cost is roughly fixed. The metered options' per-PR premium compounds —
Devin alone would run **$1.4k–$5.8k/month** vs. the Claude path's **~$175–$350**. Even if
self-hosting cost you a full **5 hrs/month of ops ($500)**, total Claude-path cost
(~$675–$850) still beats Cursor's *model spend alone*. The labor-vs-spend crossover that
red-teaming worried about only bites at low volume; at 20 PRs/week it inverts decisively
toward the cheap-per-PR path.

**The honest footnote the brief demands:** the cheap per-PR numbers still exclude *your
labor*. The crossover where managed (Remote Tasks / Cursor) wins on *total* cost is encoded
as the rollback trigger below — but at this volume you'd have to be spending **>5 hrs/month**
on glue *and* getting Cursor's spend down for it to flip. The real ceiling at 87 PRs/month
is **your review throughput**, not dollars (see Risks: reviewer overload).

## Risks, Trust Boundaries, and Rollback Criteria

### Trust boundaries
- **Agent → repo:** scoped GitHub token, branch-only write, no force-push to `main`.
- **Agent → secrets:** read from CI secret store only; gitleaks/secret-scan still runs in CI.
- **Agent → merge:** **none.** No option is granted auto-merge. PR policy bot + human review
  is the gate for every path. (Unattended merge remains unsafe in 2026.)

### Risks
- **Platform maturity:** Remote Tasks is ~2 months old; treat as fallback-capable, not sole.
- **Cost runaway (metered options):** Cursor MAX surcharge and Devin ACUs can spike silently
  → set hard monthly spend caps and alerting before enabling either.
- **Source-of-truth drift:** Copilot/GitHub-issue-centric tools fight VIBE's Linear spine.
- **Reviewer overload (the binding constraint here):** with a **solo reviewer at ~87
  PRs/month (~4–5/day)**, *your* review bandwidth — not dollars — is the bottleneck. Any
  agent can out-produce one human reviewer. Mitigate: cap in-flight agent PRs, require
  green tests before a PR requests review, and batch-review on a cadence rather than
  reacting per-PR. This is the strongest reason *not* to chase raw throughput (Devin/
  Cursor parallelism) — more PRs you can't review is negative value.

### Rollback / Flip Criteria (primary ↔ fallback)

**Confirmed thresholds (owner, 2026-05-30).** These encode the owner's tolerance for ops
time vs. model spend.

Flip **primary → Cursor Background (fallback)** if, over a 4-week trial:
- Self-hosted glue/ops exceeds **5 hours/month** at the ~$100/hr blended rate, **or**
- Per-useful-PR cost on the Claude path exceeds **$8**, **or**
- Single-issue autonomy is the bottleneck (>25% of tasks need >2 agent re-runs).

Abandon a path entirely if monthly spend breaches the configured hard cap twice, or if any
secret-leak / unwanted-dependency incident traces to the agent's PRs.

## Consequences

### Positive
- Lowest cost per *useful* PR while reusing the existing Linear/worktree/PR-policy spine.
- Optionality: managed (Remote Tasks) today, self-hosted Actions later, Cursor for bursts.
- Human-gated merge keeps the trust boundary intact.

### Negative
- We carry some platform-maturity risk on Remote Tasks.
- If the team is *not* Claude-native in practice, we leave Cursor's DX on the table.

### Neutral
- Decision is reversible: triggers and PR output are standard GitHub primitives, so swapping
  the execution engine later is low-cost.

## Related Decisions
- Blocks **VIBE-140** (downstream architecture depends on this choice).
- Related VIBE recipes: `recipes/workflows/multi-agent-coordination.md`,
  `recipes/tickets/linear-github-integration.md`.

## Notes / Sources

Pricing and benchmark figures gathered 2026-05-30; metered-billing terms change frequently
— re-verify before committing spend.

- Cursor pricing / Cloud Agents & MAX surcharge: https://www.vantage.sh/blog/cursor-pricing-explained , https://forum.cursor.com/t/what-is-the-pricing-structure-for-using-cloud-agents/156843
- Cursor Background Agent SWE-bench 65.7%: https://www.tembo.io/blog/top-coding-agent-tools
- Devin pricing (ACU $2.00–$2.25), merge rate, SWE-bench 51.5%: https://devin.ai/pricing/ , https://brainroad.com/devin-pricing-in-2026-real-cost-hidden-spend-and-alternatives/
- GitHub Copilot coding agent + usage-based shift 2026-06-01: https://github.blog/news-insights/company-news/github-copilot-is-moving-to-usage-based-billing/
- Claude Code GitHub Action (self-hosted issue→PR) + cost: https://github.com/anthropics/claude-code-action , https://code.claude.com/docs/en/github-actions
- Anthropic Remote Tasks (managed cloud, triggers, connectors) + Claude Code in Slack: https://code.claude.com/docs/en/slack , https://www.builder.io/blog/claude-code-slack
