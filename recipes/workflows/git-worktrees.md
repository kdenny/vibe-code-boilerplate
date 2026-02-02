# Git Worktrees

## When to Use This Recipe

Use this recipe when you need to:
- Work on multiple tickets simultaneously
- Keep clean separation between features
- Avoid stashing and branch switching
- Enable parallel development workflows

## What Are Worktrees?

Git worktrees let you have multiple working directories for the same repository, each checked out to a different branch.

```
your-project/           # Main working directory (main branch)
your-project-worktrees/
├── PROJ-123/           # Worktree for ticket PROJ-123
├── PROJ-456/           # Worktree for ticket PROJ-456
└── PROJ-789/           # Worktree for ticket PROJ-789
```

## Why Use Worktrees?

### Problem: Context Switching
Traditional workflow:
1. Working on feature A
2. Urgent bug comes in
3. `git stash` (hope you remember what was stashed)
4. `git checkout bug-fix`
5. Fix bug, commit, push
6. `git checkout feature-a`
7. `git stash pop` (conflicts? lost work?)

### Solution: Worktrees
With worktrees:
1. Working on feature A in `project-worktrees/PROJ-123/`
2. Urgent bug comes in
3. `vibe do PROJ-999` → creates new worktree
4. Fix bug in `project-worktrees/PROJ-999/`
5. Return to feature A in original directory

No stashing. No lost context. Parallel work.

## Using Worktrees with Vibe

### Create a Worktree
```bash
# Creates worktree and branch for a ticket
bin/vibe do PROJ-123

# Output:
# Found ticket: Fix login bug
# Branch: PROJ-123-fix-login-bug
# Worktree created at: ../your-project-worktrees/PROJ-123
#
# To start working:
#   cd ../your-project-worktrees/PROJ-123
```

### List Worktrees
```bash
git worktree list

# Output:
# /path/to/your-project                       abc1234 [main]
# /path/to/your-project-worktrees/PROJ-123    def5678 [PROJ-123]
# /path/to/your-project-worktrees/PROJ-456    ghi9012 [PROJ-456]
```

### Remove a Worktree
```bash
# After merging, clean up
git worktree remove ../your-project-worktrees/PROJ-123

# Force remove (if uncommitted changes)
git worktree remove --force ../your-project-worktrees/PROJ-123
```

## Directory Structure

By default, worktrees are created as siblings:

```
parent-directory/
├── your-project/              # Original clone
│   ├── .git/
│   ├── src/
│   └── ...
└── your-project-worktrees/    # Worktree container
    ├── PROJ-123/
    │   ├── src/
    │   └── ...
    └── PROJ-456/
        ├── src/
        └── ...
```

This is configurable in `.vibe/config.json`:

```json
{
  "worktrees": {
    "location": "sibling",
    "base_path": "../{repo}-worktrees"
  }
}
```

## Best Practices

### 1. One Ticket Per Worktree
Don't mix unrelated changes in the same worktree.

### 2. Keep Main Clean
Your main checkout should always be on `main` branch.

### 3. Regular Cleanup
Remove worktrees after PRs are merged:
```bash
# Clean up merged branches and their worktrees
git worktree prune
```

### 4. Shared Node Modules / Venv
Each worktree has its own dependencies. Consider:
- Using pnpm with shared store
- Symlinking venvs (carefully)
- Accepting the disk space trade-off

### 5. IDE Configuration
Most IDEs need to open worktrees as separate projects.

## Common Issues

### "Branch already checked out"
```
fatal: 'PROJ-123' is already checked out at '/path/to/worktree'
```
Solution: The branch is already in a worktree. Use that worktree or remove it first.

### Missing Dependencies
Each worktree needs its own `node_modules` or venv:
```bash
cd ../your-project-worktrees/PROJ-123
npm install  # or pip install -e .
```

### Git Hooks
Hooks are shared from `.git/hooks` in the main repo. This is usually what you want.

## Manual Worktree Commands

```bash
# Create worktree with new branch
git worktree add ../worktrees/feature-x -b feature-x

# Create worktree with existing branch
git worktree add ../worktrees/feature-x feature-x

# List worktrees
git worktree list

# Remove worktree
git worktree remove ../worktrees/feature-x

# Clean up stale worktree references
git worktree prune
```

## Extension Points

- Configure alternate worktree locations
- Add worktree-specific environment files
- Implement automatic cleanup workflows
