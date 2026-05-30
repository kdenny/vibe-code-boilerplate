---
title: Cursor Cloud agents — operations runbook
status: active
---

# Cursor Cloud agents — operations runbook

How the VIBE repo runs **Cursor Background (Cloud) Agents** as the short-term
issue→PR bridge, and the human controls that keep them safe: a branch-only
token, secrets in Cursor's store, a hard spend cap, and a tested kill switch.

This is the **operational** half of [VIBE-187](https://linear.app/2wrist/issue/VIBE-187).
The **technical** half — how a cloud VM boots the repo — lives in
[`.cursor/environment.json`](../../.cursor/environment.json) (built on the
warm/cold contract in
[`recipes/environments/cloud-bootstrap.md`](../../recipes/environments/cloud-bootstrap.md)).

- **Why Cursor first:** [`ADR-001`](../decisions/ADR-001-cloud-coding-agent-selection.md)
  picks self-hosted Claude as the long-term primary and Cursor as the sanctioned
  fallback; we use Cursor as the bridge to get a remote loop running *now*.
- **The program plan:** [`docs/architecture/VIBE-140-cloud-coding-environment.md`](../architecture/VIBE-140-cloud-coding-environment.md)
  (matched pair — repo doc + Linear project doc). §7 of that plan points here.

> **Trust boundary (non-negotiable, from ADR-001 + VIBE-140 §7):** the agent
> **never merges**. Every path ends at a reviewable PR into the existing gate
> (PR-policy bot + CodeRabbit + human). The token is **branch-only**; secrets
> live only in Cursor's store; spend is hard-capped; the kill switch is tested.

---

## What's automated vs. what stays human

| Surface | Automated (the agent) | Human-only (this runbook) |
|---|---|---|
| Code | Reads a ticket, branches, edits, runs `bin/ci-local`, opens a PR | — |
| Repo write | Branch-only push | Granting the token; revoking it (kill switch) |
| Secrets | Reads from Cursor's env at runtime | Storing/rotating them in Cursor |
| Spend | Consumes metered tokens | Setting the cap + alert; halting on breach |
| Merge | **Never** | Reviews and merges every PR |

---

## 1. Connect Cursor to the repo with a branch-only token

Cursor needs write access to push feature branches and open PRs — and **nothing
more**. Do **not** grant merge rights or the ability to push to `main`.

1. In Cursor → **Settings → Integrations → GitHub**, connect the
   `kevin-earl-denny` account and select **only** the
   `kevin-earl-denny/vibe-code-boilerplate` repo (least privilege; do not grant
   "all repos").
2. The repo's branch protection on `main` is the real backstop — it must
   require a PR + passing checks and **disallow direct pushes / force-pushes**
   to `main` (see §5). The token can create branches and PRs; it must not be
   able to merge or push to `main`.
   > ⚠️ **Not yet enabled (deferred to move fast) — tracked in
   > [VIBE-201](https://linear.app/2wrist/issue/VIBE-201).** Agents author PRs
   > under the owner's full-access identity, so until VIBE-201 lands this
   > boundary is **advisory** (enforced by `AGENTS.md`, not the server). VIBE-187
   > AC2 stays open until protection is live.
3. Record the date the token was granted here so rotation is auditable:
   - Granted: `<fill in>` · Granted by: `<fill in>` · Review/rotate by: `<+90d>`

**Verification (§5)** proves the scope holds before we trust it.

---

## 2. Store secrets in Cursor's secret store

Secrets the agent needs at runtime live **only** in Cursor's secret store
(exposed as env vars) — never in `.cursor/environment.json`, never in the repo,
never echoed to logs (CI's `gitleaks` scan still runs on every PR).

Cursor → **Settings → Cloud Agents → Secrets** (type: *Runtime Secret*):

| Secret | Why | Notes |
|---|---|---|
| `LINEAR_API_KEY` | Read ticket context, update status | required |
| `SLACK_BOT_TOKEN` | Slack entry point / progress (VIBE-184/188) | required for Slack triggers |
| `SLACK_SIGNING_SECRET` | Verify Slack requests (VIBE-184) | required for Slack triggers |
| `SLACK_APP_TOKEN` | Socket-mode app auth (VIBE-184) | required for Slack triggers |

> **No `ANTHROPIC_API_KEY` here.** Cursor Cloud agents run on **Cursor's own
> model billing** (MAX mode) — there is no bring-your-own Anthropic key for the
> agent's reasoning. A model key would only be needed if the *repo's own code or
> tests* called Anthropic, which VIBE's do not. (The Phase-2 self-hosted Claude
> runner is the path that uses `ANTHROPIC_API_KEY` — see VIBE-190/191.)

Confirm `.cursor/environment.json` does **not** reference or print any secret.

---

## 3. Set a hard monthly spend cap + alert

ADR-001 flags Cursor Cloud/MAX as **+20% surcharge, token-metered, and spiky**,
and encodes a cost-per-useful-PR rollback trigger. Cap before enabling.

1. Cursor → **Settings → Billing / Usage**.
2. Set a **hard monthly spend limit** (a ceiling that stops runs, not just a
   notice). Record the value:
   - Hard cap: `$<fill in>` / month · Set by: `<fill in>` · Date: `<fill in>`
3. Set a **usage alert** at a fraction of the cap (e.g. 70%) so a spike is
   visible before it hits the ceiling.
4. Cross-check spend against `bin/costs` on a cadence. Per ADR-001's rollback
   criteria, if monthly spend **breaches the cap twice**, or per-useful-PR cost
   exceeds **$8**, escalate to flipping back to the Phase-2 Claude runner.

---

## 4. Set the Linear agent guidance (team + workspace)

When a Cursor agent picks up a Linear issue it receives the issue context plus
**workspace guidance** (always injected) and **team guidance** (adherence
controlled by the integration). Keep both **DRY**: they point at each repo's
`CLAUDE.md` as the source of truth rather than duplicating it (so they can't rot
out of sync). The canonical text is below; paste it into Linear.

> Linear path — **workspace**: Settings → **AI & Agents → Workspace guidance**.
> **team**: the **VIBE team → Team agents → Optional agent guidance**.

### 4a. Workspace-level guidance (all teams — append below the repo list)

Keep the existing per-project repo mapping. Append this project-agnostic block;
it must not contain VIBE-specifics (it applies to DEAL/LIFT/PROMPT/etc. too):

```
Universal agent rules (all repos):
- The repo's CLAUDE.md is the source of truth. Read it before acting; it overrides anything here.
- One ticket = one branch = one PR, and the PR's base branch is always `main`. No stacked PRs.
- PR title carries the ticket ID (e.g. ABC-123: ...); add a risk label (Low/Medium/High Risk).
- Run the repo's local validation (its one-command check) and make it green before opening the PR.
- Never commit secrets; read credentials from the agent secret store at runtime.
- You never merge. Open a reviewable PR and stop; a human gates every merge.
```

### 4b. VIBE team-level guidance (VIBE repo only)

```
You are working in the VIBE repo: github.com/kevin-earl-denny/vibe-code-boilerplate (tracker: Linear, VIBE-*).
Read CLAUDE.md first — it is the live contract; this is only a pointer to it.

- Branch per ticket: VIBE-123-short-slug, base = main. If you depend on unmerged work, open a DRAFT PR with the DNM label, wire the Linear blocked-by edge, and rebase onto main once it lands — never stack on a non-main base.
- The VM bootstraps via .cursor/environment.json (uv venv + requirements.lock). Validate with `bin/ci-local` (or `bin/ci-local --scope` for a one-module change) and make it green before pushing.
- Open the PR per the agent-PR contract in CLAUDE.md: what changed & why, the staged step, test proof (CLI changes need a per-subcommand smoke matrix), isolation confirmation, and sync confirmation.
- Sync rule: a structural / run-flow / agent-contract change must update .coderabbit.yaml AND docs/architecture/VIBE-174-modular-restructure-plan.md in the same PR.
- You never merge. PR-policy bot + CodeRabbit + human review is the gate.
```

> Keep these blocks short on purpose. If a rule changes, change `CLAUDE.md`
> (and `.coderabbit.yaml` / the plan doc per the sync rule); only re-paste these
> pointers if the *pointer itself* changes.

---

## 5. Verify the token scope (proof, not trust)

Before relying on the agent, prove the token genuinely cannot reach `main`.
Confirm GitHub branch protection on `main`:

> **Status:** currently returns `404 "Branch not protected"` — protection is
> deferred to [VIBE-201](https://linear.app/2wrist/issue/VIBE-201). This is that
> ticket's acceptance check; it will pass once protection is enabled.

```bash
# Requires a maintainer token; read-only check of main's protection.
gh api repos/kevin-earl-denny/vibe-code-boilerplate/branches/main/protection \
  --jq '{required_pr: .required_pull_request_reviews != null,
         enforce_admins: .enforce_admins.enabled,
         allow_force_push: .allow_force_pushes.enabled,
         required_checks: .required_status_checks.contexts}'
```

Expected: `required_pr: true`, `allow_force_push: false`, and the policy/test
checks present. A direct push to `main` from the agent's token must be rejected.

---

## 6. Verify a real run opens a PR into the gate (no auto-merge)

The acceptance test. Trigger a Cursor agent on a small VIBE ticket and confirm:

1. It opens a PR with **base = `main`** on a `VIBE-…` branch.
2. **PR Policy** (`.github/workflows/pr-policy.yml`) runs — ticket ref + risk
   label checked.
3. **CodeRabbit** reviews per [`docs/review/coderabbit-policy.md`](../review/coderabbit-policy.md).
4. The PR is **not** auto-merged and **cannot** be merged by the agent — it waits
   for a human.

Record the proof PR number here: `#<fill in>`.

---

## 7. Kill switch (documented + tested)

How to **halt all Cursor agents immediately**. Test it once at setup so it's
known-good, not theoretical.

**Immediate halt (fastest first):**
1. **Stop in-flight agents:** Cursor → Background/Cloud Agents dashboard →
   **Stop / cancel** each active run.
2. **Cut spend:** set the monthly hard cap (§3) to a value at/under current
   spend, which blocks new runs.
3. **Cut repo access (hard stop):** revoke the Cursor GitHub integration's
   access to `vibe-code-boilerplate` (GitHub → Settings → Applications →
   Cursor → revoke repo access), **or** disable the Cursor agent in
   Linear (VIBE team → Team agents → Cursor → disable). Either severs the
   trigger→PR path.
4. **Rotate secrets** (§2) if a runaway may have leaked or misused a key.

**Test it:** start a trivial agent run, hit **Stop**, and confirm no further
commits/PR activity appears. Record: tested `<date>` by `<who>` — result `<ok>`.

Phase-2 (self-hosted Claude runner) has its own kill switch
(`fly scale count 0`), documented separately under VIBE-198.

---

## Related

- [`ADR-001 — Cloud Coding Agent Selection`](../decisions/ADR-001-cloud-coding-agent-selection.md)
- [`VIBE-140 — Cloud Coding Environment plan`](../architecture/VIBE-140-cloud-coding-environment.md) (§7 trust/secrets/spend/kill)
- [`.cursor/environment.json`](../../.cursor/environment.json) · [`recipes/environments/cloud-bootstrap.md`](../../recipes/environments/cloud-bootstrap.md)
- [`docs/review/coderabbit-policy.md`](../review/coderabbit-policy.md) · [`.github/workflows/pr-policy.yml`](../../.github/workflows/pr-policy.yml)
