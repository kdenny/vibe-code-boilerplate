# Slack Integration Recipe — VIBE cloud-agents app

## Overview

This recipe documents the **`VIBE Agents` Slack app**: the shared Slack surface
that **both** cloud-agent entry points hang off — the Phase 1 Cursor bridge and
the Phase 2 self-hosted Claude Code runner (trigger in, progress out, escalation,
human reply-back). It is the human-setup half of **VIBE-184** and the reproducible
runbook for standing the app up again (new workspace, rotated tokens, disaster
recovery).

It is intentionally a **HUMAN** task: Slack app creation and token issuance are
external-account actions an agent must not perform. This doc records what was
provisioned so the server-side handler (VIBE-192) and the Fly runner (VIBE-190/191)
have an exact contract to build against.

- **Parent goal:** VIBE-140 (cloud coding environment) — see the canonical plan
  `docs/architecture/VIBE-140-cloud-coding-environment.md` and ADR-001
  (`docs/decisions/ADR-001-cloud-coding-agent-selection.md`).
- **Server-side follow-ups:** VIBE-192 (Slack trigger + progress thread — the
  handler the `/vibe` Request URL points at), VIBE-190 (provision the Fly machine),
  VIBE-191 (the headless runner). **This ticket creates the app; those wire the
  server side to it.**

## Prerequisites

- Workspace admin (or app-approval) rights in the target Slack workspace.
- Access to the secret stores the runner reads: local `.env.local` (gitignored),
  GitHub Actions secrets (CI), and `fly secrets` (deploy).
- The three token **names** are declared in `.env.example`; the **values** never
  enter the repo.

## What was provisioned (current config)

| Setting | Value |
|---|---|
| App name | `VIBE Agents` |
| Bot user | enabled; **neutral identity** — display name **not** "Claude" (de-attribution, VIBE-197) |
| Event delivery | **Socket Mode enabled** (Fly runner path) **and** the Events API request-URL path documented — one app serves both engines |
| Slash command | `/vibe` (usage hint `do VIBE-123`) |
| Channel | **`#_vibe-cloud-agents`** — escalation + human reply-back surface |
| Tokens | `SLACK_BOT_TOKEN` (`xoxb-`), `SLACK_SIGNING_SECRET` (32-hex), `SLACK_APP_TOKEN` (`xapp-`) |

> **Channel-name note.** The VIBE-184 ticket and the VIBE-140 plan use the
> canonical name **`#vibe-agents`**; the channel actually created is
> **`#_vibe-cloud-agents`**. The runner is configured against the *actual* name
> (`SLACK_CHANNEL` below). Reconcile the ticket/plan to the real name, or rename
> the channel, before the gate.

## Recipe

### 1. Create the app + bot user

1. <https://api.slack.com/apps> → **Create New App** → **From scratch**.
2. Name it `VIBE Agents`; pick the workspace.
3. **App Home** → enable the **bot user**.

### 2. Bot Token Scopes (exactly these six)

Under **OAuth & Permissions → Scopes → Bot Token Scopes**, add **only**:

| Scope | Why |
|---|---|
| `commands` | the `/vibe` slash command |
| `chat:write` | post progress + escalation messages |
| `chat:write.customize` | post under a **neutral** username/avatar (not "Claude") |
| `app_mentions:read` | react to `@VIBE Agents` mentions |
| `channels:history` | read human replies in **public** channels |
| `groups:history` | read human replies in **private** channels |

**Add no User Token Scopes.** The runner acts as a *bot*, never on behalf of a
user. Requesting user scopes — or restricted scopes such as `links.embed:write` —
fails the install with *"Invalid permissions requested"* and widens the security
surface (e.g. `users:read.email` exposes member emails). Least-privilege is the
point: this exact six-scope set is what VIBE-184 specifies.

### 3. Event delivery — Socket Mode (Fly path) + Events API (HTTP)

**Socket Mode (the runner's path):**

1. **Socket Mode → Enable Socket Mode**.
2. **Basic Information → App-Level Tokens → Generate Token and Scopes**: name it
   `vibe-socket`, add scope **`connections:write`**, generate → this is the
   `xapp-` token. With Socket Mode on, the runner opens a WebSocket; no public
   ingress URL is required and slash commands route over the socket.

**Events API (HTTP), documented for the serverless / Cursor ingress:** a deployed
endpoint receives Slack POSTs and verifies them with `SLACK_SIGNING_SECRET`. Flip
the app from Socket Mode to a request URL when that ingress exists; the same app
and the same bot/signing tokens are reused (no re-provisioning). Subscribe to
`app_mention` and `message.channels` / `message.groups` events.

### 4. Slash command

**Slash Commands → Create New Command:**

- Command: `/vibe`
- Request URL: placeholder until VIBE-192 ships (e.g.
  `https://vibe-claude-runner.fly.dev/slack/command`). Slack requires a
  syntactically valid URL; the endpoint may **501** until the handler lands. Under
  Socket Mode this URL is not actually called.
- Short description: `Trigger a VIBE cloud agent on a ticket`
- Usage hint: `do VIBE-123`

Adding the command may prompt a **reinstall**; approve it — tokens are unchanged.

### 5. Channel

Create **`#_vibe-cloud-agents`** and **invite the bot**. This is the escalation +
human-in-the-loop reply-back channel (VIBE-196).

### 6. Neutral identity (de-attribution)

**App Home → Your App's Presence in Slack:** set a neutral **Display Name** /
default username (e.g. `VIBE Agents` / `vibe-agents`), **not** "Claude"; keep
"Always Show My Bot as Online" on. This is the human-visible half of the
runner-only de-attribution policy (VIBE-197).

### 7. Store the secrets (names in repo, values never)

Add the three secret **values** — plus the (non-secret) `SLACK_CHANNEL` name — to
each store the runner reads — local, CI, deploy. Locally:

```bash
# .env.local (gitignored — never commit)
SLACK_BOT_TOKEN=xoxb-…          # OAuth & Permissions → Bot User OAuth Token
SLACK_SIGNING_SECRET=…          # Basic Information → App Credentials (32 hex chars)
SLACK_APP_TOKEN=xapp-…          # Basic Information → App-Level Tokens (connections:write)
SLACK_CHANNEL=#_vibe-cloud-agents
```

```bash
# CI (GitHub Actions)
gh secret set SLACK_BOT_TOKEN
gh secret set SLACK_SIGNING_SECRET
gh secret set SLACK_APP_TOKEN
gh secret set SLACK_CHANNEL          # channel name, not a secret — set it here too so CI routing matches local

# Deploy (Fly) — set when VIBE-190 provisions the machine
fly secrets set SLACK_BOT_TOKEN=… SLACK_SIGNING_SECRET=… SLACK_APP_TOKEN=… SLACK_CHANNEL='#_vibe-cloud-agents'
```

The **names** live in `.env.example`; nothing echoes a value to logs, and the CI
secret scan (`gitleaks`) still runs on every PR.

## Verification

- **Tokens well-formed:** `SLACK_BOT_TOKEN` starts `xoxb-`, `SLACK_APP_TOKEN`
  starts `xapp-`, `SLACK_SIGNING_SECRET` is exactly 32 hex chars (watch for a
  trailing space on paste).
- **Bot auth:** `curl -s -H "Authorization: Bearer $SLACK_BOT_TOKEN"
  https://slack.com/api/auth.test` returns `"ok": true`.
- **Channel:** the bot appears in `#_vibe-cloud-agents`' member list.
- **Identity:** the bot's display name is **not** "Claude".
- **End-to-end** (`/vibe` round-trip, message post, reply-back read): **deferred
  to VIBE-192** — needs the server-side handler. Tracked there, not here.

## Handoff to the server side

VIBE-192 (handler) + VIBE-190/191 (Fly + runner) consume this app:

1. Load `SLACK_BOT_TOKEN` / `SLACK_SIGNING_SECRET` / `SLACK_APP_TOKEN` from
   `fly secrets` (VIBE-190).
2. Connect via **Socket Mode** using `SLACK_APP_TOKEN`; post with
   `SLACK_BOT_TOKEN` under the neutral identity.
3. Swap the `/vibe` **Request URL** from the placeholder to the deployed ingress
   (only if/when moving off Socket Mode to the Events API path).
4. Implement the `/vibe do VIBE-123` contract and the progress-thread / escalation
   / reply-back loop (VIBE-192, VIBE-196).

## Related

- ADR-001 — Cloud Coding Agent Selection (`docs/decisions/ADR-001-cloud-coding-agent-selection.md`)
- VIBE-140 cloud coding environment plan (`docs/architecture/VIBE-140-cloud-coding-environment.md`)
- Slack API docs: <https://api.slack.com/apps> · Socket Mode: <https://api.slack.com/apis/socket-mode>
