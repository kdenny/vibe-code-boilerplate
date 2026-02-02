# Boilerplate Feedback (Filing Issues in the Boilerplate Repo)

## When to Use This Recipe

Use this recipe when:
- You find something **broken, inconsistent, or misleading** in the project’s main agent contract file (e.g. **CLAUDE.md**) or in any file under **recipes/**
- You want to report it to the boilerplate repo so the source material can be fixed for all projects built from it

**Do this automatically.** Do not wait for the user to ask. File (or open) the issue as part of handling the problem.

## Canonical URL

- **Issues list:** https://github.com/kdenny/vibe-code-boilerplate/issues  
- **New issue:** https://github.com/kdenny/vibe-code-boilerplate/issues/new  

## How to File an Issue

1. **From the project:** Run  
   `bin/vibe boilerplate-issue --title "Brief description" --body "Details (file, section, what's wrong, optional fix)"`  
   This opens the boilerplate repo’s new-issue page in the browser with title and body pre-filled.

2. **Print URL only (e.g. in CI or headless):**  
   `bin/vibe boilerplate-issue --print-only`  
   Use with `--title` and `--body` to get a full URL to open manually or log.

3. **Config:** The project’s `.vibe/config.json` may include `boilerplate.issues_url`; the command uses that, or falls back to the canonical URL above.

## What to Include in the Issue

- **What is broken:** e.g. wrong instruction, outdated step, contradiction between CLAUDE.md and a recipe (file must be named CLAUDE.md, all caps).
- **Where:** file path and, if useful, section or line (e.g. `recipes/security/secret-management.md`, “Syncing” section).
- **Optional:** suggested fix or clarification.

## When Not to File

- Bugs or missing features in **this project’s** app code or tooling (file those in this repo).
- Questions or feature ideas that are not about boilerplate content (CLAUDE.md or recipes). Use your judgment; when in doubt, file so the boilerplate maintainers can triage.
