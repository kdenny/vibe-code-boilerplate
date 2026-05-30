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

## Be strict about (request changes)

These are real signal. CodeRabbit is configured — via `path_instructions`,
`pre_merge_checks`, and `request_changes_workflow` — to block on them:

| Area | What triggers request-changes |
|------|-------------------------------|
| **Tests** | Behavior changes without tests at the right level. Tests so mocked they don't exercise the real path. Integration tests added for modules not meant to compose. |
| **CLI changes** | No per-subcommand live smoke-test matrix in the PR description. Thin wrappers without docs. Silently swallowed CLI errors. Relying on mocked CI tests as the only proof. |
| **Module boundaries** | Increased hidden coupling, reach-through into internals, new global state, or a module that can no longer run/test in isolation. |
| **Migration posture** | Big-bang rewrites where staged extraction was viable. Large structural churn not justified by the target architecture. Behavior regressions in a refactor. |
| **Local validation** | Broken or slowed local run/validation. Anything that makes `bin/ci-local` slower or less reliable. |
| **PR metadata** | Title missing the `VIBE-<n>:` ticket ref. Description missing the staged step, test proof, isolation confirmation, or the sync confirmation. |
| **Sync rule** | A structural / run-flow / agent-contract change that does not update `.coderabbit.yaml` (and CLAUDE.md) in the same PR. |

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
- **`request_changes_workflow: true` + `abort_on_close: true`** — outcomes are
  decisive and block the merge, rather than advisory.
- **`auto_review.auto_incremental_review: true`** — re-reviews each push so the
  agent loop stays tight; latency stays low.
- **`pre_merge_checks` (title/description = error)** — hard gates that enforce the
  agent-PR contract instead of hoping authors remember it.
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
