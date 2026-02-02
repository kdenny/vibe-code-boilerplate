# CLAUDE.md – AI Agent Instructions

**Filename:** This file must be named **CLAUDE.md** (all caps) in the project root so Cursor and other tools load it as the project’s agent instructions.

This file contains instructions for AI agents (Claude, GPT, etc.) working on projects that use this boilerplate.

---

## Project Overview

**Fill this in after applying the boilerplate** so AI agents have immediate context on what the project is. Run `bin/vibe setup` when ready; consider updating this section as part of that flow.

- **What this project does:** *(e.g. "SaaS dashboard for inventory and orders")*
- **Tech stack:** *(e.g. backend: Django; frontend: React; database: PostgreSQL; deployment: Fly.io)*
- **Key features / domains:** *(e.g. auth, reporting, webhooks)*
- **Specs or docs:** *(link to ADRs, product spec, or "None yet" if they don't exist)*

---

## README Maintenance

Keep the project **README.md** accurate so humans and agents can onboard quickly.

### When a new app is initialized (from a prompt or setup)

After creating or configuring a new project, update **README.md** with:

- **App name and description** – What the project does and who it’s for
- **Tech stack** – Frameworks, runtimes, databases, deployment (align with Project Overview in this file)
- **Setup instructions** – Prerequisites, install steps, env vars, how to run locally
- **Project structure** – Short overview of key directories (e.g. `api/`, `ui/`, `scripts/`)

If the user ran `bin/vibe setup`, remind them to update README as part of the “next steps” (see setup wizard).

### Continuous maintenance

As the project evolves, keep README in sync:

- **New features** – Document user-facing or notable capabilities
- **Setup steps** – Refine when install/run steps change
- **Architecture changes** – Update structure or diagrams when layout or responsibilities change

When you add a new top-level area (e.g. a new app, service, or major script), add a brief note to README and to the Project Overview above.

See `recipes/agents/readme-maintenance.md` for the full guide.

---

## Configuration Reference

The canonical configuration is in `.vibe/config.json`. Key fields are populated when you run `bin/vibe setup` (tracker, `github.owner`, `github.repo`, etc.). Example shape:

```json
{
 "tracker": { "type": "linear", "config": { "deployed_state": "Deployed" } },
 "github": { "auth_method": "gh_cli", "owner": "<your-org>", "repo": "<your-repo>" },
 "branching": { "pattern": "{PROJ}-{num}", "always_rebase": true },
 "labels": {
 "type": ["Bug", "Feature", "Chore", "Refactor"],
 "risk": ["Low Risk", "Medium Risk", "High Risk"],
 "area": ["Frontend", "Backend", "Infra", "Docs"],
 "special": ["HUMAN", "Milestone", "Blocked"]
 }
}
```

- **tracker.config.deployed_state** (optional): State name to use when a PR is merged (e.g. `Deployed`, `Done`, `Released`). The PR-merged workflow (`.github/workflows/pr-merged.yml`) uses repo variable `LINEAR_DEPLOYED_STATE` in CI (default `Deployed`); this config key is for local use and documentation.
- **tracker.config.in_review_state** (optional): State name when a PR is opened (default: `In Review`). The PR-opened workflow (`.github/workflows/pr-opened.yml`) uses repo variable `LINEAR_IN_REVIEW_STATE` in CI.
- **tracker.config.done_state** (optional): Final "done" state name (e.g. `Done`, `Closed`). Used when UAT workflow is enabled—tickets go to `deployed_state` (e.g. `To Test`) on merge, then manually to `done_state` after verification. See `recipes/workflows/uat-testing.md`.

---

## Core Rules

### When to Ask for Clarification

**Always ask when:**
- Requirements are ambiguous or contradictory
- Multiple valid implementations exist with different trade-offs
- Security or data implications are unclear
- The task would take significant time if the wrong approach is chosen
- Destructive operations are involved

**Never ask when:**
- The answer is clearly in the codebase
- Standard patterns apply
- It's a trivial decision with easy reversal
- The question was already answered in context

See `recipes/agents/asking-clarifying-questions.md` for examples.

### When to Create HUMAN Tickets

The `HUMAN` label means "I cannot proceed without human action." Use it sparingly.

**DO create HUMAN tickets for:**
- Obtaining **actual secret values** (API keys, passwords the human must retrieve)
- External account actions (creating accounts on third-party services, enabling billing)
- Subjective decisions (UI/UX choices, branding, product direction)
- Legal/compliance review
- External communications (emails to users, public announcements)

**DO NOT create HUMAN tickets for:**
- Writing code or config files (even security-related code)
- Running CLI commands (`fly secrets set`, `gh secret set`, etc.)
- Setting up infrastructure (Dockerfiles, workflows, terraform)
- Documentation
- Architecture decisions (if requirements are clear, just implement)
- Installing dependencies or tools

**Ask yourself:** "Can I do this programmatically?" If yes, do it. If no, create a HUMAN ticket.

**Example:**
- "Provide DATABASE_URL" → HUMAN (need actual credential value)
- "Configure Fly.io secrets" → NOT HUMAN (you can run `fly secrets set`)
- "Write RLS policies" → NOT HUMAN (you can write the code)

See `recipes/agents/human-required-work.md` for the full guide.

### How to Handle Ambiguity

1. **Check context first** - Re-read the request, examine related code
2. **Make informed assumptions** - If confidence >80%, proceed with a note
3. **Ask with options** - Provide 2-3 specific options, not open-ended questions
4. **Document assumptions** - Note any assumptions in code comments or PR description

### File Editing

**No files in this repo are protected.** You may edit any file freely. Do not treat any path as read-only or off-limits; apply changes wherever they are needed to complete the task.

### Efficient Command Execution

**Prefer absolute paths and command-specific directory flags over `cd path && command`.** The latter causes sequential execution, resets shell working directory between commands, and adds unnecessary overhead.

| Avoid | Prefer |
|-------|--------|
| `cd /path && git status` | `git -C /path status` |
| `cd /path && git add . && git commit -m "..."` | `git -C /path add .` then `git -C /path commit -m "..."` (or one invocation with multiple args) |
| `cd /path && git push -u origin BRANCH` | `git -C /path push -u origin BRANCH` |
| `cd /path && npm install` | `npm --prefix /path install` |
| `cd /path && npm run build` | `npm --prefix /path run build` |
| `cd /path && gh pr create ...` | `gh pr create --repo owner/repo ...` (repo from main checkout or config; use `--head branch` if needed) |

**Worktree workflows:** When operating on a worktree (e.g. `../project-worktrees/PROJ-123`), use `git -C <worktree-path> ...` for all git commands from the main repo or from another shell. Use `gh pr create --repo owner/repo --head PROJ-123 ...` so you don't need to `cd` into the worktree to open the PR. This allows parallel or independent commands without changing directory.

---

## Ticket Management

### "Do this ticket {ticket}" – What it means

When the user says **"do this ticket PROJ-123"** (or any ticket ID), that means:

1. **Do the work on a fresh worktree** – Create a dedicated worktree for that ticket (`bin/vibe do PROJ-123`), do all work there (no work in the main checkout).
2. **Open a PR when complete** – When the work is done, commit, push, and open a PR (title with ticket ref, risk label, etc.). Do not leave the work only local.

So: **"do this ticket {ticket}"** = **do this ticket on a fresh worktree and open a PR when complete.**

### Ticketing System (Linear) Must Be Configured First

Before creating, listing, or fetching tickets, a tracker (e.g. Linear) must be configured in `.vibe/config.json`. If you or the user runs `bin/ticket create`, `bin/ticket list`, or `bin/ticket get` without a tracker configured:

- The CLI **pauses** and prints: "No ticketing system (e.g. Linear) is configured. Set up a tracker before creating or viewing tickets."
- It then prompts: **"Run tracker setup now?"** (default: yes).
- If the user confirms, it runs the tracker wizard (Linear/Shortcut/None), saves config, and the ticket command proceeds.
- If the user declines, it exits with a hint to run `bin/vibe setup` or `bin/vibe setup --wizard tracker` when ready.

When writing tickets or advising the user to create tickets, either ensure the project has already run `bin/vibe setup` (or `bin/vibe setup --wizard tracker`), or expect the interactive prompt and let the user complete it.

### Starting Work on a Ticket

When asked to "do" a ticket, use a fresh worktree and open a PR when done (see ["Do this ticket"](#do-this-ticket--ticket--what-it-means) above).

```bash
# Use the vibe CLI to create a worktree
bin/vibe do PROJ-123
```

This creates:
- A worktree at `../project-worktrees/PROJ-123/`
- A branch named according to the pattern (e.g., `PROJ-123`)

### Creating Tickets

When creating tickets programmatically:
1. **Check for duplicates first** — Search existing tickets (open and recently closed) for similar work before creating a new ticket. If a ticket already covers the same scope, update that ticket instead.
2. Use descriptive titles: "Verb + Object" format
3. **Apply labels** (see [Label checklist](#label-checklist-for-ticket-creation) below)
4. Include acceptance criteria
5. Link related tickets with **correct blocking direction** (see [Blocking relationships](#blocking-relationships) below)

#### Avoiding Duplicate Tickets

Before creating a new ticket, **always search** for existing tickets that might cover the same work:

```bash
bin/ticket list  # Review open tickets for overlap
```

**Signs of a duplicate:**
- Same component/area being modified
- Similar acceptance criteria
- Part of the same milestone or initiative
- Would result in conflicting changes if both were implemented

**If you find a potential duplicate:**
- Update the existing ticket with any new requirements
- Add a comment explaining the additional scope
- Do NOT create a new ticket

**If scopes overlap but aren't identical:**
- Consider if one ticket can be expanded to cover both
- If truly separate, document the boundary clearly in both tickets
- Link them with "related to" (not blocking)

#### Blocking relationships

Direction matters. The **prerequisite** (foundation) ticket **blocks** the dependent ticket — not the other way around.

- **"A blocks B"** = B cannot start until A is done. (A is the prerequisite.)
- **"A is blocked by B"** = A cannot start until B is done. (B is the prerequisite.)

**CORRECT:** "Initialize monorepo" BLOCKS "Set up React app"
(React app depends on monorepo being done first.)

**WRONG:** "Initialize monorepo" BLOCKED BY "Set up React app"
(That would mean monorepo can't start until React is done — backwards.)

When linking: set the **foundation ticket** as blocking the **dependent ticket(s)**. Do not set the foundation as "blocked by" the later tickets.

**When to use blocking:**
- True code dependencies (B imports from A, B needs A's API)
- HUMAN prerequisites (need credential value before next step)
- Sequential deployments (database migration before app deploy)

**When NOT to use blocking:**
- Parallel work on different files/components
- "Nice-to-have" ordering preferences
- Same milestone tickets (use milestone label instead)
- Related but independent features

**Keep the dependency graph shallow.** Deep chains slow down work. If you have A → B → C → D, consider if B and C can actually be parallel.

See `recipes/tickets/creating-tickets.md` for full guidance.

#### Label checklist for ticket creation

When creating a ticket, assign:

- **Type** (exactly one): Bug, Feature, Chore, Refactor
- **Risk** (exactly one): Low Risk, Medium Risk, High Risk
- **Area** (at least one): Frontend, Backend, Infra, Docs

Optional: **HUMAN**, **Milestone**, **Blocked** (see [Special Labels](#special-labels)).

#### Priority (Linear): use the Priority field, not labels

**Do not use P0, P1, P2, or P3 as labels.** Linear has a native **Priority** field. Set priority via that field so it works with Linear’s priority views and filters.

When creating or updating tickets, set the **Priority** field (not a label) using this mapping:

| If you mean | Set Linear Priority to |
|-------------|-------------------------|
| P0 / critical | **Urgent** |
| P1 / high | **High** |
| P2 / medium | **Medium** |
| P3 / low | **Low** |
| No priority | **No Priority** |

Labels in `.vibe/config.json` are for **type**, **risk**, and **area** only. Do not add P0/P1/P2/P3 to the label config.

### Ticket Status Updates

Update ticket status as work progresses:
- **Todo** → **In Progress**: When starting work
- **In Progress** → **In Review**: When PR is opened
- **In Review** → **Done**: When PR is merged

### HUMAN Follow-Up for Deployment Infrastructure

When a deployment infrastructure ticket is completed (e.g. added `fly.toml`, `vercel.json`, `.env.example`), create a **HUMAN-labeled follow-up ticket** so a human can set up production accounts and deploy. Use:

- **Manual:** `bin/ticket create-human-followup` (optionally `--parent PROJ-123` or `--files fly.toml --files vercel.json`)
- **Auto:** The workflow `.github/workflows/human-followup-on-deployment.yml` creates the ticket on merge to main when deployment config files were added (requires repo secrets `LINEAR_API_KEY`, `LINEAR_TEAM_ID`)

See `recipes/tickets/human-followup-deployment.md` for full guidance.

---

## Worktree Management

**Agent rule:** When the user asks to clean up worktrees, branches, or "tidy up" local state, follow the [Cleaning Up Worktrees](#cleaning-up-worktrees--follow-this-order) steps (remove worktrees first, then delete branches, then run `bin/vibe doctor`). Do not skip steps.

### Creating Worktrees

```bash
bin/vibe do PROJ-123
```

This creates a worktree (path from config, typically `../<repo>-worktrees/PROJ-123`) and a branch for that ticket.

### When to Clean Up Worktrees

**Clean up a worktree when:**
- The PR for that ticket has been **merged** to main (or the branch is no longer needed), or
- The user asks to "clean up branches/worktrees" or "tidy up".

**Do not remove a worktree** while the branch is still in use (open PR, WIP, or user is working there).

### Cleaning Up Worktrees — Follow This Order

Agents and users **must** do these steps in order whenever cleaning up after a merged PR or doing a general cleanup:

1. **Remove the worktree** (from the **main** repo checkout, not from inside the worktree):
   ```bash
   git worktree remove <path-to-worktree>
   ```
   Path is usually relative to the repo root, e.g. `../<repo>-worktrees/PROJ-123`. Use `git worktree list` to see exact paths. If the worktree has uncommitted changes and you're sure they're not needed: `git worktree remove --force <path>`.

2. **Delete the local branch** (only after the worktree is removed):
   ```bash
   git branch -d PROJ-123
   ```
   Use `-D` if the branch was merged via a merge commit and git reports "not fully merged".

3. **Sync local state** so `.vibe/local_state.json` matches reality:
   ```bash
   bin/vibe doctor
   ```

### One-Time Cleanup of Multiple Worktrees/Branches

When the user asks to "clean up local branches and worktrees":

1. From the **main** repo, run `git worktree list` and note every worktree that is **not** the main repo.
2. For each such worktree: `git worktree remove <path>` (or `--force` if needed).
3. Delete obsolete local branches (e.g. merged feature branches): `git branch -d <branch>` or `git branch -D <branch>`.
4. Run `bin/vibe doctor` to fix `.vibe/local_state.json`.

### Active Worktree State

Worktrees are tracked in `.vibe/local_state.json` (gitignored). Stale entries cause confusion; **always run `bin/vibe doctor`** after adding or removing worktrees so that state stays accurate.

---

## Multi-Agent Coordination

When multiple AI agents work on the same codebase simultaneously, follow these rules to prevent conflicts.

### Worktree Isolation (Mandatory)

**Each agent MUST use its own worktree.** Never share a working directory with another agent.

```bash
# Create a dedicated worktree for your work
bin/vibe do PROJ-123  # Creates ../repo-worktrees/PROJ-123
```

This prevents:
- Merge conflicts from concurrent edits
- Uncommitted changes being overwritten
- Branch switching interfering with other agents

### Situational Awareness

Before starting significant work, understand what's in flight:

```bash
# See all active feature branches
git fetch --all
git branch -r | grep -v 'main\|HEAD'

# See recent commits across ALL branches
git log --all --oneline --graph -20

# Check what files are being modified on other branches
git diff main...<other-branch> --name-only
```

### High-Risk Overlap Areas

These files are commonly edited and prone to conflicts:
- `CLAUDE.md` - Documentation updates
- `package.json` / `package-lock.json` - Dependencies
- `migrations/` - Database migrations (use timestamps)
- Shared components / utilities

**When touching these areas:**
1. Pull the latest `main` first
2. Make changes quickly and push
3. Consider coordinating with user if multiple agents need the same file

### File Conflict Prevention

1. **Check file history before editing:**
   ```bash
   git log --all --oneline -5 -- path/to/file.ts
   ```

2. **Avoid editing files with active changes on other branches**

3. **Keep your branch up to date:**
   ```bash
   git fetch origin main && git rebase origin/main
   ```

### Communication Signals

Since agents cannot directly communicate:

| Signal | How |
|--------|-----|
| **Claim work area** | Branch name describes scope: `PROJ-123-auth-refactor` |
| **Signal file changes** | Commit messages list affected files |
| **Warn of conflicts** | PR description notes overlap with known branches |
| **Coordinate via tracker** | Keep tickets "In Progress" so others see claimed work |

### Pre-Work Checklist

Before starting any task:
- [ ] `git fetch --all` - Get latest remote state
- [ ] `git branch -r` - Check what branches exist
- [ ] Check tracker for "In Progress" tickets
- [ ] Verify your branch is up to date with `main`
- [ ] Identify which files you'll modify
- [ ] Check those files aren't being actively modified elsewhere

See `recipes/workflows/multi-agent-coordination.md` for the full guide.

---

## PR Opening Checklist

Before opening a PR, ensure:

### Required
- [ ] Branch follows naming convention (`{PROJ}-{num}`)
- [ ] Rebased onto latest main (`git rebase origin/main`)
- [ ] All tests pass locally (if tests exist)
- [ ] PR title includes ticket reference
- [ ] Risk label selected (Low/Medium/High Risk)

### Recommended
- [ ] PR description uses template
- [ ] Testing instructions included (for non-trivial changes)
- [ ] Screenshots included (for UI changes)
- [ ] Documentation updated (if behavior changes)

### PR Template Location
`.github/PULL_REQUEST_TEMPLATE.md`

---

## Label Documentation

### Type Labels
| Label | Use When |
|-------|----------|
| **Bug** | Fixing broken functionality |
| **Feature** | Adding new functionality |
| **Chore** | Maintenance, dependencies, cleanup |
| **Refactor** | Code improvement, no behavior change |

### Risk Labels
| Label | Criteria |
|-------|----------|
| **Low Risk** | Docs, tests, typos, minor UI tweaks |
| **Medium Risk** | New features (flagged), bug fixes, refactoring |
| **High Risk** | Auth, payments, database, infrastructure |

### Area Labels
| Label | Scope |
|-------|-------|
| **Frontend** | UI, client-side code |
| **Backend** | Server, API, business logic |
| **Infra** | DevOps, CI/CD, infrastructure |
| **Docs** | Documentation only |

### Special Labels
| Label | Purpose |
|-------|---------|
| **HUMAN** | Requires human decision/action |
| **Milestone** | Part of a larger feature |
| **Blocked** | Waiting on external dependency |

### Milestones

- **Option A (recommended):** Use the **Milestone** label on tickets that are part of a larger feature, and link related tickets (blocks/blocked-by or parent/child). Keeps 1 ticket = 1 PR and works across trackers.
- **Option B:** Use Linear/Shortcut native milestones when the team already plans with them.

See `recipes/tickets/creating-tickets.md` for details.

---

## GitHub Actions Results

### Understanding CI Failures

**Always read the actual failure first.** Do not guess the cause from workflow names or assumptions.

1. **PR comments and review threads** – CodeQL and other checks post inline comments (e.g. from `github-advanced-security`). Read them to see the exact finding (e.g. "Incomplete URL substring sanitization") and the file/line.
2. **Failed run logs** – `gh pr checks <number>` to see which check failed; then `gh run view <run-id> --log-failed` (or open the failed job in the GitHub Checks tab) to read the error output.
3. **PR policy bot comment** – If the bot commented on the PR, it lists missing items (ticket reference, risk label, etc.).

Only after you know the real failure (e.g. "CodeQL alert on line 45", "missing risk label", "test X failed") should you fix it. See below for common workflows and responses.

When a workflow fails, check:

1. **security.yml**
   - Gitleaks: Secret detected in code
   - Dependency review: Vulnerable dependency in PR
   - CodeQL: Security finding in code (see PR review comments from github-advanced-security for file/line and query name, e.g. `py/incomplete-url-substring-sanitization`)

2. **pr-policy.yml**
   - Missing ticket reference in PR
   - Missing risk label
   - Branch naming violation

3. **pr-opened.yml**
   - Runs when a PR is opened or reopened; updates the Linear ticket (from branch name) to "In Review" state. Requires repo secret `LINEAR_API_KEY`. Optional repo variable `LINEAR_IN_REVIEW_STATE` (default: `In Review`). On failure, logs a warning and does not fail the job.

4. **pr-merged.yml**
   - Runs when a PR is merged; updates the Linear ticket (from branch name) to the "deployed" state. Requires repo secret `LINEAR_API_KEY`. Optional repo variable `LINEAR_DEPLOYED_STATE` (default: `Deployed`). On failure (e.g. no API key, ticket not found), logs a warning and does not fail the job.

5. **tests.yml** (if tests exist)
   - Test failure (check output for details)
   - No tests detected (may be intentional for new projects)

### Responding to CI Failures

**Secret detected:**
1. Remove the secret from code
2. If intentional, add to `.vibe/secrets.allowlist.json`
3. Rotate the exposed secret

**Missing labels:**
1. Add the required label via GitHub UI or `gh pr edit`

**CodeQL / security findings** (see PR review comments for the exact alert):
1. Read the inline comment: query ID, file, line, and "Show more details" link
2. Fix the finding (e.g. avoid URL substring checks in tests; use allowlists in production code) or add a documented suppression if it is a false positive
3. Push the fix

**Test failures** (if the project has tests):
1. Read the failure output (from logs or `gh run view ... --log-failed`)
2. Fix the failing test or the code
3. Push the fix

---

## Recipes Reference

When implementing specific features, consult these recipes:

### Workflow
- `recipes/workflows/git-worktrees.md` - Parallel development
- `recipes/workflows/branching-and-rebasing.md` - Git workflow
- `recipes/workflows/multi-agent-coordination.md` - Preventing conflicts with multiple agents
- `recipes/workflows/multi-agent-terminals.md` - Terminal setup for multiple agents (iTerm2, tmux)
- `recipes/workflows/linear-hooks.md` - Local hooks for automatic Linear updates
- `recipes/workflows/pr-opened-linear.md` - PR opened → Linear status (In Review)
- `recipes/workflows/pr-merge-linear.md` - PR merge → Linear status (Deployed)
- `recipes/workflows/uat-testing.md` - Optional UAT workflow (To Test → Done)
- `recipes/workflows/pr-risk-assessment.md` - Risk classification
- `recipes/workflows/testing-instructions-writing.md` - Testing docs

### Security
- `recipes/security/secret-management.md` - Handling secrets
- `recipes/security/permissions-hardening.md` - GitHub Actions security

### Architecture
- `recipes/architecture/adr-guide.md` - Decision records
- `recipes/architecture/alternatives-analysis.md` - Documenting options

### Tickets
- `recipes/tickets/creating-tickets.md` - Creating tickets (blocking, labels, milestones)
- `recipes/tickets/human-followup-deployment.md` - HUMAN follow-up tickets for deployment setup
- `recipes/tickets/linear-setup.md` - Linear configuration
- `recipes/tickets/shortcut.md` - Shortcut (stub)

---

## Command Reference

```bash
# Setup and health
bin/vibe setup              # Initial configuration
bin/vibe doctor             # Health check
bin/doctor                  # Alias for doctor

# Ticket operations
bin/ticket list             # List tickets
bin/ticket get PROJ-123     # Get ticket details
bin/ticket create "Title"   # Create ticket
bin/ticket create-human-followup   # Create HUMAN follow-up for deployment setup (after fly.toml, vercel.json, .env.example)

# Working on tickets ("do this ticket" = fresh worktree + open PR when done)
bin/vibe do PROJ-123        # Create worktree for ticket

# Secrets
bin/secrets list            # List secrets
bin/secrets sync            # Sync to provider
```

---

## Common Patterns

### Starting a New Feature

```bash
# 1. Get ticket details
bin/ticket get PROJ-123

# 2. Create worktree
bin/vibe do PROJ-123

# 3. Work in the worktree (or use absolute path for commands from elsewhere)
WORKTREE=../project-worktrees/PROJ-123  # or absolute path
# ... implement feature in that directory ...

# 4. Commit and push (from anywhere, using git -C)
git -C "$WORKTREE" add .
git -C "$WORKTREE" commit -m "PROJ-123: Add feature description"
git -C "$WORKTREE" push -u origin PROJ-123

# 5. Create PR (no cd needed; use --repo and --head)
gh pr create --repo owner/repo --head PROJ-123 --title "PROJ-123: Add feature" --body "..."
```

### Fixing a Bug

```bash
# 1. Create worktree
bin/vibe do PROJ-456

# 2. Fix the bug in the worktree (e.g. cd there to edit, or use your editor with the path)
# ... make changes in ../project-worktrees/PROJ-456 ...

# 3. Add tests that would have caught it
# 4. Commit with bug ticket reference (git -C from anywhere)
git -C ../project-worktrees/PROJ-456 commit -m "PROJ-456: Fix null pointer in auth flow"
```

### Handling CI Failures

**First:** Read the actual failure. Check PR comments (e.g. CodeQL inline comments from github-advanced-security), PR policy bot comment, and failed run logs. Do not guess from workflow names.

```bash
# 1. See which check failed
gh pr checks <number>

# 2. Read failed run logs (use run ID from the failed check link)
gh run view <run-id> --log-failed

# 3. If tests failed (and the project has tests), run locally
pytest  # or npm test, etc.

# 3. If secret scanning failed
# Review .vibe/secrets.allowlist.json

# 4. Fix and push
git push
```

---

## Anti-Patterns to Avoid

1. **Don't guess CI failures** - Read PR comments (CodeQL, policy bot) and failed run logs first
2. **Don't merge main into feature branches** - Always rebase
3. **Don't force push to main** - Only to feature branches
4. **Don't skip CI** - Wait for checks to pass
5. **Don't commit secrets** - Even for "testing"
6. **Don't skip risk labels** - Every PR needs one
7. **Don't create PRs without ticket references** - Link to tickets
8. **Don't work in the main checkout** - Use worktrees for ticket work.
9. **Don't leave merged worktrees around** - After a PR is merged, remove the worktree, delete the local branch, and run `bin/vibe doctor`.
10. **Don't use `cd path && command`** - Use `git -C path`, `npm --prefix path`, or `gh pr create --repo owner/repo` so commands can run without changing directory and can be parallelized when appropriate.

---

## When Things Go Wrong

### Rebase Conflicts
```bash
git rebase --abort  # Start over
# Or resolve and continue:
git add <resolved-files>
git rebase --continue
```

### Accidentally Committed a Secret
1. Remove from code immediately
2. Push the fix
3. Rotate the secret at its source
4. Consider adding to allowlist if it's actually public

### Worktree in Bad State
```bash
# From the main repo: force remove the worktree
git worktree remove --force <path-from-git-worktree-list>
# Delete the branch if needed
git branch -D PROJ-123
# Recreate if you still need to work on that ticket
bin/vibe do PROJ-123
```
See [Cleaning Up Worktrees](#cleaning-up-worktrees--follow-this-order) for the full cleanup procedure.
