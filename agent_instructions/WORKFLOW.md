# Agent Workflows

Standard workflows for AI agents working on this project.

## Starting Work on a Ticket

When asked to work on a ticket, follow these steps:

### Create Worktree
Create a dedicated workspace for the ticket.

```bash
bin/vibe do PROJ-123
```

### Read the Ticket
Understand what needs to be done.

```bash
bin/ticket get PROJ-123
```

### Implement the Work
Make changes in the worktree directory.

Navigate to the worktree and implement the required changes.

### Test Your Changes
Verify the implementation works.

Run tests and verify the changes work as expected.

### Commit Changes
Commit with a descriptive message.

```bash
git add <files>
git commit -m "PROJ-123: Brief description of changes"
```

### Create Pull Request
Open a PR when work is complete.

```bash
git push -u origin PROJ-123
bin/vibe pr
```

## Creating a Pull Request

When ready to submit work for review:

### Verify Changes
Check what will be included in the PR.

```bash
git status
git diff origin/main
```

### Push Changes
Push your branch to the remote.

```bash
git push -u origin BRANCH-NAME
```

### Create PR
Open the pull request.

```bash
bin/vibe pr
```

### Verify CI
Wait for CI checks to pass.

Check the PR page for CI status and fix any failures.

## Handling CI Failures

When CI fails on a pull request:

### Read the Failure
Check the actual error message.

```bash
gh pr checks <pr-number>
gh run view <run-id> --log-failed
```

### Fix the Issue
Address the specific failure.

Make the necessary code changes to fix the failure.

### Push the Fix
Push the fix and re-run CI.

```bash
git add <files>
git commit -m "Fix CI failure: <description>"
git push
```

## Cleaning Up After Merge

After a PR is merged:

### Remove Worktree
Clean up the worktree from the main repo.

```bash
git worktree remove <worktree-path>
```

### Delete Local Branch
Remove the local branch.

```bash
git branch -d PROJ-123
```

### Sync State
Update local state.

```bash
bin/vibe doctor
```
