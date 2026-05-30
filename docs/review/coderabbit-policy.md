# CodeRabbit Review Policy — VIBE Revamp

This note explains *why* [`.coderabbit.yaml`](../../.coderabbit.yaml) is configured
the way it is, and where the line sits between "CodeRabbit must be strict" and
"leave it to the author's judgment." It is the human-readable companion to the
machine config. **If you change the config, update this note in the same PR.**

## Objective

CodeRabbit is the standing **review firewall** for the non-destructive VIBE
revamp. It should give **decisive** approve / request-changes outcomes with strong
repo context and minimal noise, and it must be live *before* the main
restructuring work begins.

## Guardrail, not a roadblock (the verdict rule)

CodeRabbit is a **guardrail, not a serious roadblock**. The default outcome is
**approve**: once nothing blocking remains, it approves the PR even if non-blocking
nitpicks are still open.

A finding is **blocking** (request changes, fix before merge) **if and only if
future PRs will build on top of the affected thing** — i.e. the cost compounds if
it merges as-is. The reasoning: drift in a foundation propagates to every PR that
lands on it; a throwaway nit does not. So we pay to fix foundations now and let
one-off imperfections through.

This rule lives in the config as the global `path: "**"` instruction in
[`.coderabbit.yaml`](../../.coderabbit.yaml), and it is why `request_changes_workflow`
stays `true` (so the blocking set still hard-blocks) while the description/contract
`pre_merge_checks` were demoted from `error` to `warning` (format hygiene is a nudge,
not a roadblock).

## Block only what compounds (request changes)

These are the **foundational** findings future PRs build on. CodeRabbit is
configured — via the global `**` instruction, `path_instructions`, and
`request_changes_workflow` — to block on them:

| Area | What triggers request-changes |
|------|-------------------------------|
| **Tests** | Behavior changes without tests at the right level. Tests so mocked they don't exercise the real path. Integration tests added for modules not meant to compose. |
| **CLI changes** | No per-subcommand live smoke-test matrix in the PR description. Thin wrappers without docs. Silently swallowed CLI errors. Relying on mocked CI tests as the only proof. |
| **Module boundaries** | Increased hidden coupling, reach-through into internals, new global state, or a module that can no longer run/test in isolation. |
| **Migration posture** | Big-bang rewrites where staged extraction was viable. Large structural churn not justified by the target architecture. Behavior regressions in a refactor. |
| **Local validation** | Broken or slowed local run/validation. Anything that makes `bin/ci-local` slower or less reliable. |
| **PR metadata** | Title missing the `VIBE-<n>:` ticket ref (hard block — breaks ticket linkage). A PR based on a feature branch that isn't a documented draft+DNM bundle (never a valid final state). |
| **Sync rule** | A structural / run-flow / agent-contract change that does not update `.coderabbit.yaml` (and CLAUDE.md) in the same PR. |

> **Not blocking (warning only):** a thin or incomplete PR *description* — missing
> the staged step, test-proof matrix, isolation, or sync confirmation. These are
> format hygiene, not a defect future PRs inherit, so the contract `pre_merge_checks`
> run at `warning`. The *substance* behind them (tests actually exist, modules
> actually run in isolation, the sync edit is actually present) is still blocking,
> enforced via `path_instructions` on `tests/**`, `lib/vibe/**`, and `CLAUDE.md`.

## Stay open / quiet about (author's judgment)

Over-prescribing here creates noise and slows the agent loop, which the config
deliberately avoids (`profile: chill`, `poem`/`fortune`/`sequence_diagrams` off):

- Personal code-style preferences not enforced by a linter.
- Naming bikeshedding where the name is already clear.
- Micro-optimizations with no measured impact.
- Restructuring suggestions that exceed the ticket's scope (file a follow-up
  ticket instead of blocking the PR).
- Anything that would be churn for churn's sake — the revamp is non-destructive.

## The speed mandate

Independent of approve/request-changes: if CodeRabbit (or any reviewer) sees a way
to make **setup faster, validation faster, or the agent loop tighter**, it should
say so. A speed idea is worth a comment even on an otherwise-approvable PR. Encode
durable wins as follow-up tickets so they aren't lost.

## When a human still intervenes

CodeRabbit is decisive but not omniscient. Escalate to a human for: subjective
product / UX / branding decisions, secret values and external-account actions, and
any case where the correct architecture isn't derivable from the ticket. CodeRabbit
should explicitly defer (not guess) on these.

## Config knobs and the reasoning

- **`profile: chill`** — low style noise; strictness comes from `path_instructions`,
  not from a nitpicky global profile.
- **`request_changes_workflow: true` + `abort_on_close: true`** — kept on so the
  *blocking* set (the compounding findings) still hard-blocks the merge. The
  guardrail-not-roadblock behavior comes from narrowing *what* is blocking (the
  global `**` instruction), not from making review advisory.
- **`auto_review.auto_incremental_review: true`** — re-reviews each push so the
  agent loop stays tight; latency stays low.
- **`pre_merge_checks` (title = error; description + Agent-PR contract = warning)**
  — only the title (ticket linkage) and base-branch facts hard-block, because they
  compound; description/contract completeness is a warning nudge, not a roadblock.
- **`tone_instructions` ≤ 250 chars** — CodeRabbit silently falls back to the
  default config if any field exceeds its schema `maxLength` (tone_instructions is
  capped at 250). `tests/test_coderabbit_config.py` guards this so an over-limit
  edit can't quietly disable the whole firewall.
- **`assess_linked_issues` / `related_issues` / `related_prs`** — pulls repo and
  ticket context into every review so feedback is grounded.
- **`path_filters`** — excludes `docs/archive/**`, lockfiles, `.venv`, and build
  output so review attention goes to real changes.

## Guardrails honored

Per the originating ticket (VIBE-138), this config deliberately **does not**:
overfit to one temporary directory layout (instructions key off durable seams like
`lib/vibe/**`, `bin/**`, `tests/**`); encode personal style preferences; raise
review latency to the point of slowing agent loops; or encourage destructive
rewrites without staged validation.
