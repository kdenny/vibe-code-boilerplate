---
title: Fly.io Claude Code runner — provisioning runbook
status: active
---

# Fly.io Claude Code runner — provisioning runbook

How to provision the **Fly.io machine** that hosts the self-hosted, headless
Claude Code issue→PR runner, and the human controls that keep it safe: a
persistent volume for warm runs, secrets in `fly secrets` (never the repo), a
hard spend cap, and a tested kill switch.

This is the **operational** half of [VIBE-190](https://linear.app/2wrist/issue/VIBE-190)
— the external-account steps (app/billing/secret creation) a human must run.
The **technical** half — the app identity, machine size, volume, and non-secret
config — is declared in
[`deploy/fly/runner/fly.toml`](../../deploy/fly/runner/fly.toml).

- **Why a self-hosted runner:** [`ADR-001`](../decisions/ADR-001-cloud-coding-agent-selection.md)
  picks self-hosted Claude Code as the long-term **primary** (cheaper per useful
  PR than the Cursor bridge); this Fly machine is where it runs.
- **The program plan:** [`docs/architecture/VIBE-140-cloud-coding-environment.md`](../architecture/VIBE-140-cloud-coding-environment.md)
  (matched pair — repo doc + Linear project doc). §4.2 describes this Fly
  topology; §7 the trust/secrets/spend/kill controls.

> **Trust boundary (from ADR-001 + VIBE-140 §7):** the runner **never merges** —
> every path ends at a reviewable PR into the existing gate (PR-policy bot +
> CodeRabbit + human); secrets live only in `fly secrets`; the GitHub token is
> **branch-scoped with no merge rights**; spend is hard-capped; the kill switch
> is tested. This is **non-negotiable operating policy**.

> **Scope of this ticket (VIBE-190 = provisioning only).** This runbook gets the
> app, machine, volume, and secrets *in place* so the runtime can assume they
> exist. It does **not** build the runner image or the headless loop — that is
> [VIBE-191](https://linear.app/2wrist/issue/VIBE-191) (and it owns secret
> *consumption*). The richer observability + per-run spend tracking is
> [VIBE-198](https://linear.app/2wrist/issue/VIBE-198); §6 here documents only
> the day-one kill switch + hard cap that provisioning must guarantee.

---

## What's automated vs. what stays human

| Surface | Automated (the runner, VIBE-191+) | Human-only (this runbook) |
|---|---|---|
| Code | Reads a ticket, branches, edits, runs `bin/ci-local`, opens a PR | — |
| Infra | Boots on the provisioned machine + volume | Creating the app, machine, volume |
| Repo write | Branch-only push | Issuing the branch-scoped token; revoking it |
| Secrets | Reads from `fly secrets` at runtime (VIBE-191) | Setting/rotating them via `fly secrets set` |
| Spend | Consumes metered Anthropic + Fly compute | Setting the cap + alert; halting on breach |
| Merge | **Never** | Reviews and merges every PR |

Prereqs: the `fly` CLI (`brew install flyctl`) and `fly auth login`; use the
[`fly` skill](../../.claude/commands/fly.md) for the guided steps. The Slack
trio comes from the `VIBE Agents` app provisioned in **VIBE-184**
([`recipes/integrations/slack.md`](../../recipes/integrations/slack.md)).

---

## 1. Create the Fly app

Create the app in the VIBE org, matching the name declared in `fly.toml`. Do
**not** deploy yet — there is no runner image until VIBE-191.

```bash
# From repo root. --no-deploy: provision the app without a build (no image yet).
fly launch --no-deploy --copy-config --name vibe-claude-runner \
  --config deploy/fly/runner/fly.toml --region iad
```

If `fly launch` insists on generating its own config, create the app directly
and keep the committed `fly.toml` as the source of truth:

```bash
fly apps create vibe-claude-runner --org <vibe-org>
```

Record: app `vibe-claude-runner` · org `personal` · created `2026-05-31` by `kdenny37`.
(No machine runs yet — the app is provisioned but not deployed; the machine lands
with the runner image in VIBE-191.)

---

## 2. Choose + record the machine size

The size lives in [`deploy/fly/runner/fly.toml`](../../deploy/fly/runner/fly.toml)
(`[[vm]]`): **`shared-cpu-2x`, 2 shared CPUs, 4096 MB** — a documented starting
point sized for one Claude Code session + `bin/ci-local` (Node CLI + a uv venv +
pytest). Start small; resize only with evidence.

```bash
fly scale show -a vibe-claude-runner          # confirm the running size
fly scale vm shared-cpu-2x --memory 4096 -a vibe-claude-runner   # adjust if needed
```

If you change the size, **update `fly.toml`'s `[[vm]]` block in the same change**
so the committed config stays the source of truth. Record: size `<fill in>` ·
set `<date>`.

---

## 3. Attach the persistent volume (warm-cache contract)

The volume holds the cloned repo + dependency cache — what makes warm runs cheap
(feeds the warm/cold bootstrap budget in
[`recipes/environments/cloud-bootstrap.md`](../../recipes/environments/cloud-bootstrap.md),
VIBE-185). It mounts at `/data` per `fly.toml`'s `[mounts]`.

```bash
fly volumes create vibe_runner_data --size 10 --region iad -a vibe-claude-runner
fly volumes list -a vibe-claude-runner        # confirm it exists + region matches
```

Keep the volume **region == `primary_region`** (`iad`); a volume in another
region won't attach to the machine. Record: volume `vibe_runner_data`
(`vol_rnzmp1j5kek9gmpr`) · 10 GB · `iad` · encrypted · created `2026-05-31`.

---

## 4. Inject secrets via `fly secrets` (values only — never in the repo)

Set every secret the runner needs at runtime. Values go **only** into
`fly secrets` (encrypted, exposed as env vars on the machine) — never in
`fly.toml`, never in the repo, never echoed to logs (CI's `gitleaks` scan still
runs on every PR). The **names** match [`.env.example`](../../.env.example).

```bash
fly secrets set -a vibe-claude-runner \
  ANTHROPIC_API_KEY=sk-ant-... \
  LINEAR_API_KEY=lin_api_... \
  GITHUB_TOKEN=... \
  SLACK_BOT_TOKEN=xoxb-... \
  SLACK_SIGNING_SECRET=... \
  SLACK_APP_TOKEN=xapp-...
# SLACK_CHANNEL=#_vibe-cloud-agents is config, not a secret — it lives in
# fly.toml's [env] block, not here.
```

| Secret | Source | Used for |
|---|---|---|
| `ANTHROPIC_API_KEY` | Anthropic console | Headless Claude Code session (VIBE-191) |
| `LINEAR_API_KEY` | Linear → Settings → API (same key the local CLIs use) | Read/update tickets, wire `blocked-by` edges, post progress |
| `GITHUB_TOKEN` | GitHub — **branch-scoped, no merge rights** | Clone, push feature branches, open PRs |
| `SLACK_BOT_TOKEN` (`xoxb-`) | VIBE-184 app — OAuth & Permissions | Post progress / escalation as the bot |
| `SLACK_SIGNING_SECRET` | VIBE-184 app — Basic Information | Verify Events API requests |
| `SLACK_APP_TOKEN` (`xapp-`, `connections:write`) | VIBE-184 app — App-Level Tokens | Socket Mode websocket |

The **GitHub token must be branch-scoped with no merge rights** — the runner
pushes feature branches and opens PRs; it must not be able to push to or merge
`main` (matches the trust boundary). Record token grant + rotation date with the
rest of the VIBE-184/secret inventory.

> **As-built (2026-05-31).** 4 of 6 secrets imported from `.env.local` via
> `grep '^(LINEAR_API_KEY|SLACK_*)=' .env.local | fly secrets import -a
> vibe-claude-runner` (Staged — they apply on the first deploy in VIBE-191):
> `LINEAR_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_APP_TOKEN`.
> The two **not** in `.env.local` remain unset and are tracked as their own HUMAN
> tickets: `ANTHROPIC_API_KEY` → [VIBE-210](https://linear.app/2wrist/issue/VIBE-210),
> branch-scoped `GITHUB_TOKEN` → [VIBE-211](https://linear.app/2wrist/issue/VIBE-211).
> (`bin/secrets sync -p fly` was not used: it resolves the app from project config,
> not this new app, and syncs the whole env file with no key subset — a DX gap
> worth a follow-up if env→Fly sync becomes routine.)

---

## 5. Verify the provisioning (proof, not trust)

Confirm everything the acceptance criteria require, without leaking values.

```bash
fly status -a vibe-claude-runner              # app + machine reachable; size shown
fly volumes list -a vibe-claude-runner        # vibe_runner_data present, region iad
fly secrets list -a vibe-claude-runner        # NAMES + digests only — never values
```

`fly secrets list` must show **all six**: `ANTHROPIC_API_KEY`, `LINEAR_API_KEY`,
`GITHUB_TOKEN`, `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_APP_TOKEN`
(it prints names + content digests, never the secret values). Record the
verification: `<date>` by `<who>` — result `<ok>`.

> **As-built (2026-05-31).** `fly secrets list` shows **4 of 6** Staged
> (`LINEAR_API_KEY`, `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_APP_TOKEN`);
> `ANTHROPIC_API_KEY` (VIBE-210) + `GITHUB_TOKEN` (VIBE-211) still pending. App +
> volume confirmed via `fly status` / `fly volumes list`. All six present is the
> bar before VIBE-191's first deploy.

---

## 6. Kill switch + hard spend cap (documented + tested)

How to **halt the runner immediately** and bound spend. Test the kill switch
once at setup so it is known-good, not theoretical. (Ongoing observability +
per-run cost tracking is built on top of this by **VIBE-198**.)

**Immediate halt (fastest first):**

```bash
fly scale count 0 -a vibe-claude-runner       # scale to zero — no machine runs
fly machine stop  <machine-id> -a vibe-claude-runner   # stop a specific in-flight machine
fly machine list  -a vibe-claude-runner        # find the id(s)
```

Harder stops, if a runaway may have leaked or misused a key:
- **Cut the trigger:** revoke / rotate `SLACK_APP_TOKEN` (kills the Socket Mode
  trigger) and `GITHUB_TOKEN` (kills repo write) via `fly secrets set`.
- **Rotate** any secret in §4 that may be compromised.

**Hard spend cap (two layers — Fly compute + Anthropic tokens):**
1. **Fly compute** — the largest guardrail is **scale-to-zero when idle**
   (resting state) plus the small `[[vm]]` size. Set a Fly **spend-management /
   billing alert** in the Fly dashboard (Organization → Billing) and record:
   hard alert `$<fill in>`/month · set `<date>`.
2. **Anthropic tokens** — set a monthly usage limit on the `ANTHROPIC_API_KEY`'s
   workspace in the Anthropic console; record: limit `$<fill in>`/month.
3. Cross-check spend against `bin/costs` on a cadence (the Fly cost provider is
   `lib/vibe/costs/providers/fly.py`). Per ADR-001's rollback criteria, a
   sustained per-useful-PR cost above the threshold escalates back to the Cursor
   bridge.

**Test it:** start the machine, run `fly scale count 0`, and confirm no machine
remains (`fly machine list` shows none running). Record: tested `<date>` by
`<who>` — result `<ok>`.

---

## Related

- [`ADR-001 — Cloud Coding Agent Selection`](../decisions/ADR-001-cloud-coding-agent-selection.md)
- [`VIBE-140 — Cloud Coding Environment plan`](../architecture/VIBE-140-cloud-coding-environment.md) (§4.2 Fly topology · §7 trust/secrets/spend/kill)
- [`deploy/fly/runner/fly.toml`](../../deploy/fly/runner/fly.toml) (the technical half) · [`recipes/deployment/fly-io.md`](../../recipes/deployment/fly-io.md) (general Fly guidance)
- [`recipes/environments/cloud-bootstrap.md`](../../recipes/environments/cloud-bootstrap.md) (warm/cold bootstrap, VIBE-185) · [`recipes/integrations/slack.md`](../../recipes/integrations/slack.md) (Slack app, VIBE-184)
- [`docs/operations/cursor-cloud-agents-runbook.md`](cursor-cloud-agents-runbook.md) (the Phase-1 sibling runbook)
