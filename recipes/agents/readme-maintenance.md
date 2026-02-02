# README Maintenance

## When to Use This Recipe

Use this recipe when:
- A new app or project is initialized (from a prompt or after `bin/vibe setup`)
- You add a major feature, new top-level directory, or change how the project runs
- Setup steps, tech stack, or architecture have changed
- You want to remind humans or agents to keep README in sync

## The Problem

Stale READMEs waste time: wrong setup steps, missing env vars, outdated structure. Agents and new contributors rely on README for context. Keeping it accurate is part of project hygiene.

## When to Update README

### 1. When a new app is initialized (from a prompt or setup)

After creating or configuring a new project, update **README.md** with:

| Section | What to include |
|--------|------------------|
| **App name and description** | What the project does, who it’s for, one short paragraph |
| **Tech stack** | Frameworks, runtimes, databases, deployment (align with CLAUDE.md Project Overview) |
| **Setup instructions** | Prerequisites, install steps, env vars, how to run locally |
| **Project structure** | Short overview of key directories (e.g. `api/`, `ui/`, `scripts/`) |

If the user ran `bin/vibe setup`, the wizard already reminds them to update README in the “Next steps” list.

### 2. Continuous maintenance (as the project evolves)

Keep README in sync when you:

- **Add or change features** – Document user-facing or notable capabilities
- **Change setup or run steps** – Update prerequisites, install, env, or run commands
- **Change architecture** – Update structure, diagrams, or responsibility boundaries
- **Add a new top-level area** – New app, service, or major script → add a brief note to README and to CLAUDE.md Project Overview

## Implementation Options

### Agent instructions (CLAUDE.md)

The boilerplate adds a **README Maintenance** section to CLAUDE.md so agents:

- Update README when initializing a new app (name, description, tech stack, setup, structure)
- Keep README updated as the project evolves (features, setup, architecture)

See the README Maintenance section in your project’s CLAUDE.md.

### Setup workflow (`bin/vibe setup`)

`bin/vibe setup` includes “Update README.md with app name, description, tech stack, and setup instructions” in the **Next steps** after setup (both auto-configured and full wizard). No extra tooling required.

### Optional: Pre-commit or checklist reminder

If you use pre-commit or a PR checklist, you can add a reminder:

- **Pre-commit**: A hook that only *reminds* (e.g. “Did you update README if setup or structure changed?”) — avoid auto-editing README in a hook.
- **PR template**: Add a checklist item: “README updated if setup, structure, or notable behavior changed.”

The boilerplate does not add a pre-commit hook by default; use the recipe and CLAUDE.md as the main drivers.

## Checklist (new app or major change)

- [ ] App name and short description in README
- [ ] Tech stack listed (and matches CLAUDE.md Project Overview)
- [ ] Setup instructions: prerequisites, install, env, run
- [ ] Project structure section updated
- [ ] CLAUDE.md Project Overview updated if applicable

## Extension Points

- **Monorepos**: Keep a root README with high-level structure and links to per-package READMEs.
- **API projects**: Document main endpoints or link to OpenAPI/spec; keep setup and run steps current.
- **Templates**: If this repo is a template, keep README and CLAUDE.md as the single source of truth for “what to fill in” after clone.
