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

### Ticket Status Updates

Update ticket status as work progresses:
- **Todo** → **In Progress**: When starting work
- **In Progress** → **In Review**: When PR is opened
- **In Review** → **Done**: When PR is merged

---

## Worktree Management

### Creating Worktrees

```bash
bin/vibe do PROJ-123
```

### Cleaning Up Worktrees

After a PR is merged:
```bash
git worktree remove ../project-worktrees/PROJ-123
```

### Active Worktree State

Worktrees are tracked in `.vibe/local_state.json`:
```json
{
  "active_worktrees": [
    "../project-worktrees/PROJ-123",
    "../project-worktrees/PROJ-456"
  ]
}
```

Clean up stale entries with `bin/vibe doctor`.

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

# Working on tickets
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
7. **Don't work in the main checkout** - Use worktrees

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
# Force remove
git worktree remove --force ../project-worktrees/PROJ-123
# Recreate
bin/vibe do PROJ-123
```
