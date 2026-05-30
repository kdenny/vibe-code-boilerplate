---
description: Start working on a ticket by creating a dedicated git worktree and branch
---

# /do - Start working on a ticket

Start working on a ticket by creating a dedicated git worktree and branch.

## Usage

```
/do PROJ-123
/do 42          # GitHub issue number
```

## What it does

1. Fetches the latest `origin/main`
2. Creates a worktree at `../<repo>-worktrees/<ticket-id>/`
3. Creates a branch named after the ticket
4. Updates `.vibe/local_state.json` to track the worktree
5. Moves the ticket to **In Progress** in Linear so the board reflects that work has started (best-effort — if the tracker call fails it warns and continues; if no Linear tracker is configured it skips this step silently; it never blocks worktree creation)

## Instructions

When the user invokes `/do <ticket_id>`:

1. Run `bin/vibe do <ticket_id>` to create the worktree
2. Report the worktree path to the user
3. Remind them to work in that directory (or use absolute paths)
4. If Linear is configured, fetch and display the ticket details

## Example

```bash
bin/vibe do PROJ-123
# Output: Created worktree at ../project-worktrees/PROJ-123
#         Branch: PROJ-123
#         Ready to work!
```

## After completing work

When work is done:
1. Commit changes: `git -C <worktree-path> commit -m "PROJ-123: Description"`
2. Push branch: `git -C <worktree-path> push -u origin PROJ-123`
3. Open PR: `gh pr create --repo owner/repo --head PROJ-123 --title "PROJ-123: Title"`

Or use `/pr` to automate PR creation.
