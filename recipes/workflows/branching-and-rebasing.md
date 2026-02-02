# Branching and Rebasing

## When to Use This Recipe

Use this recipe when you need to:
- Understand the "always rebase" policy
- Keep a clean git history
- Avoid merge commits in your workflow

## The Core Rule

**Always rebase. Never merge into feature branches.**

```bash
# Good: Rebase onto main
git rebase main

# Bad: Merge main into your branch
git merge main  # Creates merge commits, messy history
```

## Why Rebase?

### Clean History
```
# With merge commits (messy):
*   Merge branch 'main' into feature
|\
| * Main commit 3
* | Feature commit 2
* | Feature commit 1
|/
* Main commit 2
* Main commit 1

# With rebase (clean):
* Feature commit 2
* Feature commit 1
* Main commit 3
* Main commit 2
* Main commit 1
```

### Benefits
- Easier to understand what changed
- Simpler `git bisect` debugging
- Cleaner PR diffs
- Linear, readable history

## Daily Workflow

### Starting Work
```bash
# Make sure main is current
git checkout main
git pull origin main

# Create feature branch
git checkout -b PROJ-123
```

### Before Creating PR
```bash
# Fetch latest main
git fetch origin main

# Rebase onto main
git rebase origin/main

# Force push (required after rebase)
git push --force-with-lease
```

### Handling Conflicts
```bash
# During rebase, if conflicts occur:
# 1. Fix conflicts in files
# 2. Stage fixes
git add <fixed-files>

# 3. Continue rebase
git rebase --continue

# If things go wrong, abort and try again
git rebase --abort
```

## Branch Naming

Follow the pattern in `.vibe/config.json`:

```
{PROJ}-{num}           → PROJ-123
{PROJ}-{num}-{desc}    → PROJ-123-fix-login
feature/{PROJ}-{num}   → feature/PROJ-123
```

### Examples
```bash
# Good branch names
PROJ-123
PROJ-123-add-user-auth
PROJ-456-fix-payment-bug

# Bad branch names
fix-stuff
johns-branch
wip
```

## Force Push Safety

After rebasing, you must force push. Use `--force-with-lease` for safety:

```bash
# Safe force push (fails if others pushed)
git push --force-with-lease

# Dangerous force push (overwrites everything)
git push --force  # Avoid this
```

## Interactive Rebase

Clean up commits before PR:

```bash
# Squash/reorder last 3 commits
git rebase -i HEAD~3
```

Options in interactive rebase:
- `pick` - Keep commit as-is
- `squash` - Combine with previous commit
- `fixup` - Combine, discard message
- `reword` - Change commit message
- `drop` - Remove commit

### Example: Squash WIP Commits
```
# Before
* WIP
* more wip
* actual feature implementation
* fix typo

# Interactive rebase → squash WIP
pick abc123 actual feature implementation
squash def456 fix typo
squash ghi789 more wip
squash jkl012 WIP

# After
* Add user authentication feature
```

## Stacked PRs

For large features, use stacked branches:

```
main
└── PROJ-123-base       # Foundation PR
    └── PROJ-123-part2  # Builds on base
        └── PROJ-123-part3  # Builds on part2
```

Rebase each onto its parent, not main:
```bash
git checkout PROJ-123-part2
git rebase PROJ-123-base

git checkout PROJ-123-part3
git rebase PROJ-123-part2
```

## Configuration

In `.vibe/config.json`:
```json
{
  "branching": {
    "pattern": "{PROJ}-{num}",
    "main_branch": "main",
    "always_rebase": true
  }
}
```

## Troubleshooting

### "Cannot rebase: You have unstaged changes"
```bash
git stash
git rebase origin/main
git stash pop
```

### "Rebase conflict on every commit"
You might have diverged significantly. Consider:
```bash
# Create a new branch with squashed changes
git checkout main
git checkout -b PROJ-123-v2
git merge --squash PROJ-123
git commit -m "All changes from PROJ-123"
```

### "Force push rejected"
Someone else pushed. Fetch and re-rebase:
```bash
git fetch origin
git rebase origin/PROJ-123
git push --force-with-lease
```

## Extension Points

- Add pre-push rebase checks
- Configure branch protection rules
- Implement automated rebase bots
