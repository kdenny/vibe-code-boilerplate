# HUMAN Follow-Up Tickets for Deployment Infrastructure

## When to Use This Recipe

Use this when:
- An agent (or human) has completed a **deployment infrastructure ticket** (e.g. added `fly.toml`, `vercel.json`, `.env.example`)
- You want a **HUMAN-labeled follow-up ticket** with clear, step-by-step instructions for a non-technical person to set up production accounts and deploy

The boilerplate can **auto-create** this follow-up ticket when such a PR is merged, or you can create it manually.

---

## 1. Manual Creation (CLI)

After finishing a deployment infra ticket, from the repo (or worktree):

```bash
# Detect deployment configs from repo and create HUMAN follow-up ticket
bin/ticket create-human-followup

# With parent ticket context (for "follow-up from PROJ-123")
bin/ticket create-human-followup --parent PROJ-123

# From a list of changed files (e.g. after a merge)
bin/ticket create-human-followup --files fly.toml --files vercel.json --files .env.example

# Print the ticket body only (don't create in tracker)
bin/ticket create-human-followup --print-only
```

**Requirements:** Tracker (e.g. Linear) configured in `.vibe/config.json`, or in CI: `LINEAR_API_KEY` and `LINEAR_TEAM_ID` env vars.

The created ticket has:
- **Title:** "Set up production infrastructure (human follow-up)"
- **Labels:** Chore, Infra, HUMAN
- **Description:** Step-by-step instructions for Vercel, Fly.io, env vars, plus a verification checklist

---

## 2. Auto-Creation on Merge (GitHub Action)

The workflow `.github/workflows/human-followup-on-deployment.yml` runs on **push to `main`**. If the push includes any of:

- `fly.toml`
- `vercel.json`
- `.env.example`

and repo secrets are set, it creates the HUMAN follow-up ticket automatically.

### Enabling Auto-Creation

1. In your GitHub repo: **Settings → Secrets and variables → Actions**
2. Add:
   - **LINEAR_API_KEY** – Linear API key (from Linear → Settings → API)
   - **LINEAR_TEAM_ID** – Linear team UUID (from team URL or API)

If these secrets are not set, the workflow still runs but skips ticket creation and logs a message.

---

## 3. What the Generated Ticket Contains

The ticket body includes:

- **Prerequisites** – Password manager access, payment method, GitHub access
- **Context** – Optional parent ticket reference
- **Steps** – Only for detected platforms:
  - **Vercel** – Sign in, add project, import repo, set env vars, deploy
  - **Fly.io** – Install CLI, `fly launch`, secrets, `fly deploy`
  - **Env** – Copy `.env.example`, fill from team secrets, never commit
- **Verification** – Checklist: web app loads, API health, workers, no secrets committed

Links to official docs (Vercel, Fly.io) are included.

---

## 4. Customization

- **Env path:** Use `--env-path` if your template is not `.env.example` (e.g. `apps/web/.env.example`).
- **Template:** The body is built in `lib/vibe/deployment_followup.py`; you can extend `DEPLOYMENT_INDICATORS` or `build_human_followup_body()` for more platforms (e.g. Neon, Supabase).

---

## Related Recipes

- `recipes/tickets/creating-tickets.md` – Labels, blocking, milestones
- `recipes/deployment/vercel.md` – Vercel deployment
- `recipes/deployment/fly-io.md` – Fly.io deployment
- `recipes/agents/human-required-work.md` – When to use the HUMAN label
