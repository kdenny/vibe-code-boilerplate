# CLAUDE.md – AI Agent Instructions

**Filename:** This file must be named **CLAUDE.md** (all caps) in the project root so Cursor and other tools load it as the project’s agent instructions.

This file contains instructions for AI agents (Claude, GPT, etc.) working on projects that use this boilerplate.

---

## Minimal Prompts / Using This Repo as Reference

When the user gives a **minimally specified prompt** that references this boilerplate (e.g. "Build an app for X using https://github.com/kdenny/vibe-code-boilerplate"), apply these conventions **automatically** without requiring the user to list them:

- **Project structure conventions** – `.vibe/`, `bin/`, `lib/`, `recipes/`, `.github/` as in this repo
- **Git workflow** – Worktrees for ticket work (`bin/vibe do PROJ-123`), branch naming `{PROJ}-{num}`, rebase (never merge main into feature branches)
- **PR templates and policies** – Risk labels, ticket reference in title, template in `.github/PULL_REQUEST_TEMPLATE.md`
- **Ticket tracking integration** – Linear (or configured tracker), labels (type, risk, area), "do this ticket" = worktree + PR when done

Do not ask the user to enumerate these bullets; they are implied by "use this boilerplate" or "use vibe-code-boilerplate". Use the **recipes/** directory for step-by-step implementations (workflows, security, tickets, etc.).

---

## Project Overview

**Fill this in after applying the boilerplate** so AI agents have immediate context on what the project is. Run `bin/vibe setup` when ready; consider updating this section as part of that flow.

- **What this project does:** *(e.g. "SaaS dashboard for inventory and orders")*
- **Tech stack:** *(e.g. backend: Django; frontend: React; database: PostgreSQL; deployment: Fly.io)*
- **Key features / domains:** *(e.g. auth, reporting, webhooks)*
- **Specs or docs:** *(link to ADRs, product spec, or "None yet" if they don't exist)*

---

## Configuration Reference

The canonical configuration is in `.vibe/config.json`. Key fields are populated when you run `bin/vibe setup` (tracker, `github.owner`, `github.repo`, etc.). Example shape:

```json
{
  "tracker": { "type": "linear", "config": {} },
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

### When to Block and Request Human Review

Apply the `HUMAN` label and stop when:
- Security decisions (auth changes, access control)
- Financial/legal implications
- External communications (user-facing copy)
- Major architecture decisions
- Tasks requiring credentials you don't have
- Subjective judgment calls (UI/UX, branding)

See `recipes/agents/human-required-work.md` for the full guide.

### How to Handle Ambiguity

1. **Check context first** - Re-read the request, examine related code
2. **Make informed assumptions** - If confidence >80%, proceed with a note
3. **Ask with options** - Provide 2-3 specific options, not open-ended questions
4. **Document assumptions** - Note any assumptions in code comments or PR description

### File Editing

**No files in this repo are protected.** You may edit any file freely. Do not treat any path as read-only or off-limits; apply changes wherever they are needed to complete the task.

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
1. Use descriptive titles: "Verb + Object" format
2. **Apply labels** (see [Label checklist](#label-checklist-for-ticket-creation) below)
3. Include acceptance criteria
4. Link related tickets with **correct blocking direction** (see [Blocking relationships](#blocking-relationships) below)

#### Blocking relationships

Direction matters. The **prerequisite** (foundation) ticket **blocks** the dependent ticket — not the other way around.

- **"A blocks B"** = B cannot start until A is done. (A is the prerequisite.)
- **"A is blocked by B"** = A cannot start until B is done. (B is the prerequisite.)

**CORRECT:** "Initialize monorepo" BLOCKS "Set up React app"  
(React app depends on monorepo being done first.)

**WRONG:** "Initialize monorepo" BLOCKED BY "Set up React app"  
(That would mean monorepo can't start until React is done — backwards.)

When linking: set the **foundation ticket** as blocking the **dependent ticket(s)**. Do not set the foundation as "blocked by" the later tickets.

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

When a workflow fails, check:

1. **security.yml**
   - Gitleaks: Secret detected in code
   - Dependency review: Vulnerable dependency in PR
   - CodeQL: Security issue in code

2. **pr-policy.yml**
   - Missing ticket reference in PR
   - Missing risk label
   - Branch naming violation

3. **tests.yml** (if tests exist)
   - Test failure (check output for details)
   - No tests detected (may be intentional for new projects)

### Responding to CI Failures

**Secret detected:**
1. Remove the secret from code
2. If intentional, add to `.vibe/secrets.allowlist.json`
3. Rotate the exposed secret

**Missing labels:**
1. Add the required label via GitHub UI or `gh pr edit`

**Test failures** (if the project has tests):
1. Read the failure output
2. Fix the failing test or the code
3. Push the fix

---

## Recipes Reference

When implementing specific features, consult these recipes:

### Workflow
- `recipes/workflows/git-worktrees.md` - Parallel development
- `recipes/workflows/branching-and-rebasing.md` - Git workflow
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

# 3. Navigate to worktree
cd ../project-worktrees/PROJ-123

# 4. Implement feature...

# 5. Commit and push
git add .
git commit -m "PROJ-123: Add feature description"
git push -u origin PROJ-123

# 6. Create PR
gh pr create --title "PROJ-123: Add feature" --body "..."
```

### Fixing a Bug

```bash
# 1. Create worktree
bin/vibe do PROJ-456

# 2. Fix the bug
cd ../project-worktrees/PROJ-456
# ... make changes ...

# 3. Add tests that would have caught it
# 4. Commit with bug ticket reference
git commit -m "PROJ-456: Fix null pointer in auth flow"
```

### Handling CI Failures

```bash
# 1. Check what failed
gh pr checks

# 2. If tests failed (and the project has tests), run locally
pytest  # or npm test, etc.

# 3. If secret scanning failed
# Review .vibe/secrets.allowlist.json

# 4. Fix and push
git push
```

---

## Anti-Patterns to Avoid

1. **Don't merge main into feature branches** - Always rebase
2. **Don't force push to main** - Only to feature branches
3. **Don't skip CI** - Wait for checks to pass
4. **Don't commit secrets** - Even for "testing"
5. **Don't skip risk labels** - Every PR needs one
6. **Don't create PRs without ticket references** - Link to tickets
7. **Don't work in the main checkout** - Use worktrees for ticket work.
8. **Don't leave merged worktrees around** - After a PR is merged, remove the worktree, delete the local branch, and run `bin/vibe doctor`.

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
