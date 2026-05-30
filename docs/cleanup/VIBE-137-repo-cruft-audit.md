# VIBE-137 — Repo Cruft Audit & Validated Cleanup List

**Ticket:** [VIBE-137 — Remove repo cruft before scaling cloud agents](https://linear.app/2wrist/issue/VIBE-137/remove-repo-cruft-before-scaling-cloud-agents)
**Deliverable:** a validated cleanup list grouped into **delete / extract / consolidate / defer**, plus the safe deletes and the modular-testing infrastructure executed in this PR.

## Goal

Validate and remove repo cruft that will slow down remote agents, create noisy
context, or increase review churn — before we scale cloud coding agents. This is
an audit; every finding is bucketed and either **done in this PR** (low-risk) or
**deferred** (tracked, or staged behind the module rewrites).

## How it was validated

Four parallel read-only sweeps over the worktree (hardcoded refs / stale stack;
duplicate docs & instruction sources; test-suite bloat; tooling duplication & PR
automation), then each candidate was re-verified by hand before bucketing.
Findings that touch behavior were checked against the revamp contract in
`CLAUDE.md` ("preserve behavior; stage, don't big-bang").

---

## Summary

| Bucket | Items | This PR |
|--------|-------|---------|
| **Delete** | 3 confirmed-dead files | ✅ executed |
| **PR-automation hardening** | 2 (exact ticket matching; stale-branch pruning) | ✅ executed |
| **Extract** | 2 (cost-provider HTTP layer; tracker shared HTTP) | ⏸️ defer to existing VIBE-86 line |
| **Consolidate** | 2 (test thinning; fallback-workflow docs) | ◑ 1 demonstrated, rest tracked |
| **Defer** | 1 (regenerate instruction files post-revamp) | ⏸️ revamp-exit checklist |

Plus the **modular-testing infrastructure** the audit's test findings depend on:
module-scoped CI (`lib/vibe/testscope.py` + `tests.yml`) and the policy recipe.

> **Scope note:** we support **Linear only** now, so the "tracker-aware" parsing
> concern collapses to Linear-aware exact matching (below). The `bin/` venv
> bootstrap duplication is **dropped from this audit** — it's being handled in
> `.direnv` once VIBE-176 merges.

---

## DELETE — executed in this PR

Confirmed dead; removed via `git rm`. All recoverable from history or by
regeneration.

| File | Why it's cruft | Verification |
|------|----------------|--------------|
| `.cursorrules` | Legacy single-file Cursor format, **superseded** by the curated `.cursor/rules/*.mdc` rules. Contains only stale `(your project name)` template placeholders (`Generated: 2026-04-01`) that misrepresent this repo. | `.cursor/rules/` holds two real `.mdc` rules; Cursor reads that directory. The root file is dead drift. |
| `.github/copilot-instructions.md` | Same stale `2026-04-01` template with placeholder content. Regeneration is **disabled during the revamp** (CLAUDE.md is the hand-authored source), so this file actively feeds misleading context to any agent/IDE that reads it. | Recoverable any time via `bin/vibe generate-agent-instructions` once the revamp ends. |
| `docs/superpowers/specs/2026-04-01-cli-view-aliases-design.md` | One-off design spec for `--view` / `--unblocked` on `bin/ticket list`. **The feature shipped** — the spec is now stale scratch. | `--view`/`--unblocked` implemented in `lib/vibe/cli/ticket.py:139-205`. |

**Not deleted (considered, rejected as unsafe):**

- `.github/workflows/pr-opened.yml`, `pr-merged.yml` (fallback Linear integration).
  These look like dead cruft *if* `github_integration: "native"`, but `.vibe/config.json`
  is **not checked in** (projects create it at setup), so the setting is unknowable
  at the repo level, and these are shipped boilerplate that downstream projects use
  in fallback mode. Deleting would remove a supported path. → **Consolidate** (docs), below.
- `recipes/observability/sentry.md`, `recipes/databases/neon.md` — these are correct
  **redirect stubs** to the canonical recipes, not duplication. Keep.
- `docs/archive/CLAUDE.boilerplate.md` — intentional rollback archive, referenced by
  CLAUDE.md. Keep.

---

## PR-AUTOMATION HARDENING — executed in this PR

These are PR-automation edge cases (the ticket's fifth dimension) that produce
"noisy or incorrect" PRs as remote agents scale. Both fixed in `lib/vibe/cli/main.py`
with tests in `tests/test_duplicate_pr_prevention.py`.

| Fix | Before | After |
|-----|--------|-------|
| **Exact ticket matching** (`_check_existing_prs_for_ticket`) | Substring match — `gh pr list --search VIBE-1` returns VIBE-12 / VIBE-100, and `"VIBE-1" in title` flagged them all as duplicates → false-positive abort prompts. | Word-boundary regex (`\bVIBE-1\b`, case-insensitive). VIBE-1 no longer matches VIBE-12; still matches `VIBE-1:` and `Fixes VIBE-1`. |
| **Stale-branch pruning** (`_check_local_state_for_ticket_conflicts`) | Warned on *any* other recorded branch for the ticket, including ones abandoned weeks ago — noise at agent scale. | Records older than `_STALE_BRANCH_DAYS` (30) are treated as abandoned and ignored, using the existing `created_at` timestamp. Missing/unparseable timestamps fail-safe (kept). |

> **Overlap with [VIBE-22](https://linear.app/2wrist/issue/VIBE-22):** the exact-matching
> fix *is* VIBE-22's scope ("fix exact ticket matching in open-PR duplicate detection").
> Done here at the user's direction — **VIBE-22 can be closed as resolved by this PR.**

## EXTRACT — defer to the existing extraction line (VIBE-86 et al.)

These are genuinely reusable seams, but extraction is already the subject of
[VIBE-86](https://linear.app/2wrist/issue/VIBE-86) /
[VIBE-99](https://linear.app/2wrist/issue/VIBE-99). Folding them in there avoids
a competing ticket and keeps the module-boundary work in one place.

| Candidate | Detail | Recommendation |
|-----------|--------|----------------|
| Cost-provider HTTP/auth boilerplate | All 8 providers under `lib/vibe/costs/providers/` repeat `_headers()` + `os.environ.get("<X>_API_KEY")` + ad-hoc `requests` error handling, with no shared retry. | Extract a thin `costs` HTTP helper **when** `costs/` is restructured. Note as a sub-item under VIBE-86's scope. |
| Tracker HTTP/GraphQL execution | `trackers/*` repeat query-execution + auth patterns. | Already in VIBE-86's stated scope ("shared Linear/Neon/Axiom/Fly tooling"). No new ticket. |

> Both are premature to extract before the module-boundary revamp stabilizes — a
> generic wrapper now would be thin and would churn surface the rewrites will
> touch anyway.

---

## CONSOLIDATE

### C1 — Test-suite thinning (the big one)

The suite is **~10,086 lines across 33 files**. The sweep found heavy
redundancy concentrated in the tracker and CLI suites: private-method tests,
near-identical cases written longhand instead of parametrized, and over-mocking
that asserts "the mock was called" rather than real behavior. Estimated
reducible: **~2,000–2,500 lines** without losing real coverage.

**Decision: do NOT gut these in this PR.** Two reasons rooted in the contract:

1. **It's exactly the "big-bang churn" CLAUDE.md says to split.** Rewriting
   ~2,250 lines of tests across a dozen files is large-surface churn without a
   staged justification.
2. **The modules are being rewritten anyway.** A module's tests should be
   **re-leveled in the same PR as its rewrite** (kept as the rewrite's contract,
   with internals-pinning tests dropped), not pre-emptively gutted in a separate
   PR that splits the contract from the code it guards.

**What this PR does instead** — builds the rails so the per-rewrite thinning is
cheap and enforced, and demonstrates the pattern once:

- **Module-scoped CI** (`lib/vibe/testscope.py` + `tests.yml`): PRs run only the
  changed modules' tests; `main` + shared-file changes run the full suite.
- **Policy** in [`recipes/testing/modular-testing.md`](../../recipes/testing/modular-testing.md),
  enforced by `.coderabbit.yaml` (`tests/**` path instruction).
- **Demonstration:** `tests/test_update_check.py::TestCompareVersions` collapsed
  from 8 longhand functions to one parametrized test — same 8 cases, ~half the
  lines, zero coverage change.

**Per-module thinning targets** (apply during each module's rewrite, per the policy):

| Suite | Lines | Action when its module is rewritten |
|-------|-------|-------------------------------------|
| `test_trackers_linear.py` | 1306 | Drop `_get_label_ids` / `_parse_issue` / `_get_workflow_state_id` private-method tests; parametrize the ~5 case-insensitive-label tests. |
| `test_trackers_shortcut.py` | 891 | Parametrize `_list_*_filter` variants; keep public CRUD. |
| `test_trackers_github_issues.py` | 663 | Merge filter-construction variants into one parametrized test. |
| `test_cli_ticket.py` | 998 | Parametrize redundant create/list variants; assert structured output, not output strings. |
| `test_views.py` | 421 | Fold into `test_trackers_linear.py` (views is a Linear feature) — keep all cases. |
| `test_tools.py`, `test_ui_*.py`, `test_costs_provider_vercel.py`, `test_update_check.py` | — | De-mock UI/widget tests; parametrize; mock at the boundary. |

**Keep as-is (high-value, behavioral, low-mock):** `test_retrofit.py`,
`test_config.py`, `test_duplicate_pr_prevention.py`, `test_label_sync.py`,
`test_doctor.py`, `test_frontend.py`, `test_agents.py`, `test_git_worktrees.py`,
`test_secrets_providers.py`.

### C2 — `bin/` venv bootstrap duplication — DROPPED

`bin/ticket`, `bin/costs`, `bin/secrets` each repeat ~20 lines of venv
detection/activation/dispatch. This is **no longer an audit item**: bootstrap is
moving to `.direnv` once **VIBE-176** merges, which removes the per-script venv
plumbing entirely. No follow-up needed.

### C3 — Fallback-workflow guidance

`pr-opened.yml` / `pr-merged.yml` can fire **alongside** native Linear
integration if a project keeps `LINEAR_API_KEY` set after switching to native —
duplicate API calls / noise. → Strengthen the "fallback only — delete if using
native" preamble in both workflows (doc-only; **track as follow-up**).

---

## DEFER — tracked, not in scope here

| Item | Detail | Tracking |
|------|--------|----------|
| **Regenerate instruction files** | After the revamp, re-enable `bin/vibe generate-agent-instructions` and regenerate `.cursor/rules` + copilot instructions from `agent_instructions/` with real project context. | Revamp-exit checklist. |

> The duplicate-PR exact-match and stale-branch items that were originally here
> are now **done in this PR** (see *PR-automation hardening* above). The
> tracker-aware parsing concern is resolved by Linear-only exact matching.

---

## Verification

- `bin/ci-local --fast`: **786 passed, 9 skipped**; ruff check, ruff format, mypy,
  gitleaks all clean (after formatting).
- `lib/vibe/testscope.py`: 25 unit tests; CLI entrypoint smoke-tested across
  full / scoped / empty / stdin / fail-safe modes.
