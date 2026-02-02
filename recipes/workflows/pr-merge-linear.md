# PR merge → Linear ticket status (Deployed)

When a PR is merged, the workflow `.github/workflows/pr-merged.yml` automatically updates the associated Linear ticket to a "deployed" state (e.g. **Deployed**, **Done**, **Released**).

This is the companion to [pr-opened-linear.md](pr-opened-linear.md) which handles the `In Progress → In Review` transition when PRs are opened.

## Complete Linear Workflow

```
Backlog → In Progress → In Review → Deployed
           (manual)     (PR opened) (PR merged)
```

## Setup

1. **Repository secret**
   - Add `LINEAR_API_KEY` in the repo: **Settings → Secrets and variables → Actions → New repository secret**.
   - Use a Linear API key with write access (e.g. from [Linear → Settings → API](https://linear.app/settings/api)).

2. **Target state (optional)**
   - Default state name is **Deployed**.
   - To use a different state (e.g. **Done**, **Released**), add a repository **variable** (not secret): **Settings → Secrets and variables → Actions → Variables → New repository variable**:
     - Name: `LINEAR_DEPLOYED_STATE`
     - Value: exact state name as in your Linear workflow.

3. **Branch naming**
   - The workflow only updates a ticket when the merged PR’s **branch name** starts with a ticket ID (e.g. `PROJ-123` or `PROJ-123-add-feature`). If the branch doesn’t match, the job does nothing.

## Behavior

- Runs on `pull_request` with `types: [closed]`, only when `merged == true`.
- Extracts ticket ID from the PR head branch (pattern `^[A-Z]+-[0-9]+`).
- Looks up the issue in Linear by identifier, resolves the team’s workflow state by name, and updates the issue’s state.
- If anything fails (no API key, ticket not found, state name not found), the job **logs a warning and exits successfully** so the merge is not blocked.

## Manual fallback

If the workflow isn’t configured or you need to move a ticket manually:

```bash
bin/ticket update PROJ-123 --status "Deployed"
```

Use the exact state name your Linear workflow uses (e.g. **Done**, **Released**).

## Config (local)

In `.vibe/config.json`, `tracker.config.deployed_state` is optional and used for local/documentation; the GitHub Actions workflow uses the repo variable `LINEAR_DEPLOYED_STATE` (default `Deployed`).

## UAT Workflow (Optional)

If your team uses a testing step before marking tickets done, set `LINEAR_DEPLOYED_STATE` to your testing state (e.g. `To Test`, `QA`, `Staging`). After verification, manually move tickets to `Done`.

See [uat-testing.md](uat-testing.md) for full UAT workflow documentation.

## Related

- [pr-opened-linear.md](pr-opened-linear.md) - Updates ticket to In Review when PR is opened
- [uat-testing.md](uat-testing.md) - Optional UAT workflow (To Test → Done)
- [linear-setup.md](../tickets/linear-setup.md) - Initial Linear configuration
