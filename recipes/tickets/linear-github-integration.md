# Linear GitHub Integration (Native)

This guide walks you through enabling Linear's native GitHub integration, which automatically syncs PR status with your Linear tickets.

## Why Native Integration?

Linear provides a first-party GitHub integration that:

- **One-click OAuth setup** - No API keys to manage in CI
- **Automatic PR linking** - PRs automatically attach to tickets based on branch names
- **Bidirectional sync** - See PR status in Linear, see ticket status in GitHub
- **Auto-close on merge** - Tickets move to Done when PRs are merged
- **Maintained by Linear** - Bug fixes and new features without updating your repo

This is simpler and more reliable than custom GitHub Actions workflows.

## Prerequisites

- Linear workspace with admin access
- GitHub repository with admin access
- Branch naming convention that includes ticket IDs (e.g., `PROJ-123-add-feature`)

## Step-by-Step Setup

### Step 1: Open Linear Integrations

1. Open Linear (linear.app)
2. Click your workspace name in the top-left
3. Select **Settings**
4. Navigate to **Integrations** in the left sidebar
5. Find and click **GitHub**

### Step 2: Connect GitHub Account

1. Click **Connect GitHub**
2. You'll be redirected to GitHub to authorize Linear
3. Choose which organization/account to connect:
   - Select your organization if working on a team repo
   - Select your personal account for personal repos
4. Click **Authorize Linear**

### Step 3: Select Repositories

After authorization, you'll see a list of repositories:

1. Find your repository in the list
2. Toggle the switch to enable it
3. Repeat for any additional repos you want to connect

### Step 4: Configure Auto-Close (Recommended)

Linear can automatically move tickets to Done when PRs are merged:

1. In Linear Settings → Integrations → GitHub
2. Find **Auto-close issues**
3. Enable the toggle
4. Select your target state (e.g., "Done", "Deployed", "Closed")

### Step 5: Configure Branch Linking

Linear automatically links branches that contain a ticket ID. Ensure your workflow uses the correct branch naming:

**Supported patterns:**
- `PROJ-123` - Exact ticket ID
- `PROJ-123-add-feature` - Ticket ID prefix with description
- `feature/PROJ-123` - Ticket ID anywhere in branch name

**Not supported:**
- `add-feature-123` - No project prefix
- `proj-123` - Lowercase (must match Linear's case)

## Workflow Comparison

| Event | Native Integration | Custom Workflows (old) |
|-------|-------------------|----------------------|
| PR opened | Shows "PR Open" badge in Linear | Moved ticket to "In Review" |
| PR merged | Moves to configured state | Moved ticket to "Deployed" |
| PR linked | Automatic from branch name | Automatic from branch name |
| Setup | One OAuth click | API keys + repo variables |
| Maintenance | Linear handles | You maintain workflow files |

## What You See

### In Linear

When a PR is opened for ticket PROJ-123:
- The ticket shows a **GitHub PR** attachment
- PR status badge: "Open", "In Review", "Merged"
- Link to the PR for quick access
- (If auto-close enabled) Ticket moves to Done on merge

### In GitHub

When viewing a PR:
- Linear ticket is linked in PR description (if you include ticket ID)
- GitHub Checks show Linear status (optional)

## Verifying the Setup

1. Create a test branch with a ticket ID:
   ```bash
   bin/vibe do PROJ-123  # or any existing ticket
   ```

2. Make a small change and push:
   ```bash
   echo "# Test" >> test.md
   git -C ../vibe-code-boilerplate-worktrees/PROJ-123 add test.md
   git -C ../vibe-code-boilerplate-worktrees/PROJ-123 commit -m "PROJ-123: Test Linear integration"
   git -C ../vibe-code-boilerplate-worktrees/PROJ-123 push -u origin PROJ-123
   ```

3. Open a PR on GitHub

4. Check Linear - the ticket should show a PR attachment within seconds

5. Merge the PR - the ticket should move to your configured "done" state

## Troubleshooting

### PR Not Linking

**Symptom:** PR is open but doesn't appear in Linear ticket.

**Fixes:**
1. Verify branch name contains ticket ID in correct format (e.g., `PROJ-123`, not `proj-123`)
2. Check Linear Settings → Integrations → GitHub and verify the repo is enabled
3. Try disconnecting and reconnecting the GitHub integration

### Ticket Not Moving on Merge

**Symptom:** PR merged but ticket stays in same state.

**Fixes:**
1. Check Linear Settings → Integrations → GitHub → Auto-close issues is enabled
2. Verify the target state is correctly configured
3. Check the ticket isn't in a terminal state (already Done/Cancelled)

### "Not Authorized" in Linear

**Symptom:** GitHub shows as disconnected in Linear.

**Fixes:**
1. Your GitHub OAuth token may have expired
2. Go to Linear Settings → Integrations → GitHub
3. Click **Reconnect** or **Disconnect** then **Connect GitHub** again

### Integration Not Showing

**Symptom:** GitHub option missing from Linear integrations.

**Fixes:**
1. Check you have admin access to the Linear workspace
2. Some workspaces have integrations disabled - contact your workspace admin
3. Try a different browser or clear cache

## Local Hooks (Optional Enhancement)

The native GitHub integration handles PR events. For even faster feedback during development, you can optionally enable local Claude Code hooks:

```bash
cp .claude/settings.local.json.example .claude/settings.local.json
```

This adds:
- **Mention ticket in prompt** → Marks ticket "In Progress"
- **Git commit with ticket ID** → Marks ticket "Done"

See [linear-hooks.md](../workflows/linear-hooks.md) for details.

## Migration from Custom Workflows

If you were using the custom `pr-opened.yml` and `pr-merged.yml` workflows:

1. **Delete the workflows** (already done if using this boilerplate)
2. **Remove repo secrets/variables:**
   - `LINEAR_API_KEY` (repo secret) - no longer needed for this purpose
   - `LINEAR_DEPLOYED_STATE` (repo variable) - configure in Linear instead
   - `LINEAR_IN_REVIEW_STATE` (repo variable) - not needed with native integration
3. **Keep your LOCAL `.env.local`** - still needed for local ticket operations

## Related

- [linear-setup.md](linear-setup.md) - Initial Linear configuration and labels
- [linear-hooks.md](../workflows/linear-hooks.md) - Optional local hooks for faster feedback
