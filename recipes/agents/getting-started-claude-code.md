# Getting Started with Claude Code + Vibe Boilerplate

This guide walks you through your first session using Claude Code with a project that uses the vibe-code-boilerplate.

## Prerequisites

- Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- A project with this boilerplate applied (CLAUDE.md exists in root)
- Git repository initialized

## Your First Session

### Step 1: Health Check

Start every new project session with a health check:

```bash
/doctor
```

This validates your configuration, checks tool installations, and verifies integrations are working.

### Step 2: See Available Work

```bash
/ticket list --status "Todo,Backlog"
```

This shows tickets from your configured tracker (Linear or Shortcut).

### Step 3: Start Working on a Ticket

```bash
/do PROJ-123
```

This creates a dedicated worktree and branch for the ticket. You work in isolation — no risk of messing up `main`.

### Step 4: Do the Work

Claude Code reads CLAUDE.md automatically, so it understands your project's conventions. Just describe what you need:

- "Implement the authentication middleware described in PROJ-123"
- "Fix the bug: users can't log in with special characters in passwords"
- "Add the API endpoint for listing orders with pagination"

### Step 5: Open a PR

```bash
/pr
```

This creates a pull request with the right template, ticket reference, and labels.

### Step 6: Clean Up After Merge

Once your PR is merged:

```bash
/cleanup
```

This removes the worktree and local branch.

## Key Concepts

### CLAUDE.md Is Your Instruction Manual

The `CLAUDE.md` file in your project root is loaded automatically by Claude Code. It contains:
- Project-specific conventions
- Available commands and workflows
- Label taxonomy and PR requirements
- Integration configuration

### Worktrees Keep You Safe

Every ticket gets its own worktree (a separate copy of the repo). This means:
- You can work on multiple tickets simultaneously
- No risk of uncommitted changes from one task affecting another
- Clean separation between features

### Slash Commands Are Your Friends

| Command | What It Does |
|---------|-------------|
| `/do PROJ-123` | Start work on a ticket |
| `/pr` | Open a pull request |
| `/ticket list` | See available tickets |
| `/ticket create "Title"` | Create a new ticket |
| `/doctor` | Check project health |
| `/cleanup` | Remove merged worktrees |

## Common First-Session Mistakes

1. **Working in main** — Always use `/do` to create a worktree
2. **Forgetting ticket references** — PRs need a ticket ID in the title
3. **Skipping risk labels** — Every PR needs a risk label (Low/Medium/High)
4. **Not running doctor first** — Catches config issues before they cause problems
5. **Leaving worktrees around** — Clean up after PRs are merged

## Next Steps

- Read `recipes/agents/effective-prompting.md` for better results
- Read `recipes/workflows/git-worktrees.md` for advanced worktree usage
- Read `recipes/workflows/branching-and-rebasing.md` for the git workflow
