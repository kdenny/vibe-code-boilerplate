# Common Errors and Solutions

Quick fixes for the most common issues you'll encounter.

## "No ticketing system (e.g. Linear) is configured"

**Cause:** No tracker configured in `.vibe/config.json`.

**Fix:**
```bash
bin/vibe setup --wizard tracker
```

## "LINEAR_API_KEY not set"

**Cause:** The Linear API key is not available as an environment variable.

**Fix:**
```bash
# Add to your .env.local file
echo "LINEAR_API_KEY=lin_api_xxxxx" >> .env.local

# Or export directly
export LINEAR_API_KEY=lin_api_xxxxx

# Then verify
bin/vibe doctor
```

## "Branch already exists"

**Cause:** A local branch with that name already exists (from a previous attempt or another worktree).

**Fix:**
```bash
# Check if there's an existing worktree using it
git worktree list

# If the worktree exists and is no longer needed
git worktree remove ../project-worktrees/PROJ-123
git branch -d PROJ-123

# Then retry
bin/vibe do PROJ-123
```

## "Worktree already exists"

**Cause:** A worktree at that path already exists.

**Fix:**
```bash
# Force remove the stale worktree
git worktree remove --force ../project-worktrees/PROJ-123

# Clean up the branch
git branch -D PROJ-123

# Sync state
bin/vibe doctor

# Retry
bin/vibe do PROJ-123
```

## "Failed to create PR"

**Cause:** Usually one of:
- Not authenticated with `gh` CLI
- Branch not pushed to remote
- Already a PR open for this branch

**Fix:**
```bash
# Check gh auth
gh auth status

# Push branch if needed
git push -u origin BRANCH_NAME

# Check for existing PR
gh pr list --head BRANCH_NAME

# Retry
bin/vibe pr
```

## "Config validation error"

**Cause:** `.vibe/config.json` has invalid or missing fields.

**Fix:**
```bash
# Run doctor to see what's wrong
bin/vibe doctor

# Check config manually
cat .vibe/config.json | python -m json.tool

# Re-run setup to fix
bin/vibe setup
```

## "Permission denied" on bin/ scripts

**Cause:** Scripts don't have execute permission.

**Fix:**
```bash
chmod +x bin/vibe bin/ticket bin/secrets bin/doctor
```

## Rebase Conflicts

**Cause:** Your branch diverged from main.

**Fix:**
```bash
# Option 1: Resolve conflicts
git rebase origin/main
# Fix conflicts in each file
git add <resolved-files>
git rebase --continue

# Option 2: Start over (if changes are small)
git rebase --abort
git stash
git rebase origin/main
git stash pop
```

## "Not a git repository"

**Cause:** Running commands outside a git repo, or in a broken worktree.

**Fix:**
```bash
# Check where you are
pwd
git status

# If in a worktree that's broken
cd /path/to/main/repo
git worktree repair
```

## Tests Failing in CI

**Cause:** Various — always read the actual error first.

**Fix:**
```bash
# See which check failed
gh pr checks PR_NUMBER

# Read the failure logs
gh run view RUN_ID --log-failed

# Run tests locally
pytest  # or npm test, etc.
```

## Further Help

- Run `bin/vibe doctor` for a comprehensive health check
- Check `recipes/` for detailed guides on specific topics
- Report boilerplate bugs: `bin/vibe boilerplate-issue`
