# Linear GitHub Integration (Native)

Linear provides a native GitHub integration that automatically links PRs to issues, updates ticket status, and syncs information between the two platforms. This is the **recommended** approach for most teams.

## Why Native Integration?

| Feature | Native Integration | Custom Workflows |
|---------|-------------------|------------------|
| Setup complexity | One OAuth click | Configure secrets, variables |
| Maintenance | Maintained by Linear | You maintain the code |
| PR linking | Automatic | Branch name parsing |
| Status updates | Automatic | Custom workflow triggers |
| Issue sync | Bidirectional | One-way only |
| Branch detection | Smart matching | Regex patterns |

**Recommendation**: Use native integration. Only use custom workflows if you have specific requirements (self-hosted GitHub, custom state mapping, etc.).

## Setup Guide

### Step 1: Connect GitHub to Linear

1. In Linear, go to **Settings** (gear icon or avatar → Settings)
2. Navigate to **Integrations** in the left sidebar
3. Find **GitHub** and click **Connect**
4. Authorize Linear to access your GitHub organization
5. Select the repositories you want to integrate

### Step 2: Configure Auto-Link Settings

After connecting, configure how Linear links to GitHub:

1. Go to **Settings → Integrations → GitHub**
2. For each connected repository:
   - **Auto-link issues**: Enable to link branches/PRs to issues
   - **Auto-close issues**: Enable to close issues when PRs merge
   - **Sync comments**: Enable to sync PR comments to Linear

### Step 3: Configure Workflow Automation

Linear can automatically update issue status based on PR events:

1. Go to **Settings → Integrations → GitHub**
2. Click on your repository
3. Under **Workflow automation**:
   - **When PR is opened**: Set to "In Review" (or your equivalent)
   - **When PR is merged**: Set to "Done" or "Deployed"
   - **When PR is closed (not merged)**: Optionally set to "Cancelled"

### Step 4: Branch Naming

For automatic linking, use Linear issue IDs in branch names:

```
ENG-123              # Matches issue ENG-123
ENG-123-add-feature  # Also matches
feature/ENG-123      # Also matches (Linear is smart)
```

Linear will detect the issue ID anywhere in the branch name.

## How It Works

### PR Opens → Issue Updates

When you open a PR with a branch like `ENG-123-add-auth`:

1. Linear detects the issue ID from the branch name
2. Adds a link to the PR on the Linear issue
3. Updates the issue status to "In Review" (if configured)
4. Syncs PR title/description to Linear (optional)

### PR Merges → Issue Closes

When the PR is merged:

1. Linear detects the merge event
2. Updates the issue status to "Done" or "Deployed"
3. Adds a completion note with merge details

### Comments Sync

If enabled, PR review comments sync to the Linear issue, keeping all discussion in one place.

## Verification

After setup, verify the integration works:

1. Create a branch with a Linear issue ID: `git checkout -b ENG-123-test`
2. Make a small change and push
3. Open a PR on GitHub
4. Check the Linear issue - it should show:
   - A link to the PR
   - Status changed to "In Review" (if configured)

## Comparison with Custom Workflows

### When to Use Native Integration

- Standard GitHub.com repositories
- Default Linear workflow states
- Want zero maintenance

### When to Use Custom Workflows (Fallback)

- GitHub Enterprise Server (self-hosted)
- Custom state names not matching Linear's expected values
- Need to trigger other actions beyond status updates
- Want to support non-Linear trackers (Shortcut) with same workflow

The custom workflows (`pr-opened.yml`, `pr-merged.yml`) are kept in this boilerplate as a fallback for these cases.

## Disabling Custom Workflows

If using native integration, you can disable the custom workflows:

### Option 1: Delete the Files

```bash
rm .github/workflows/pr-opened.yml
rm .github/workflows/pr-merged.yml
```

### Option 2: Disable via GitHub UI

1. Go to **Repository Settings → Actions → General**
2. Under "Workflow permissions", you can disable specific workflows
3. Or rename files to `.yml.disabled`

### Option 3: Keep as Fallback

Leave them in place. They check for `LINEAR_API_KEY` and skip gracefully if not set. If you're using native integration, just don't set the secret.

## Troubleshooting

### PR Not Linking to Issue

- Verify the branch name contains a valid Linear issue ID
- Check that the GitHub repository is connected in Linear
- Ensure the issue exists and isn't archived

### Status Not Updating

- Check **Settings → Integrations → GitHub → Workflow automation**
- Verify the state names match your Linear workflow
- Look for error messages in Linear's integration logs

### Integration Disconnected

- Re-authorize at **Settings → Integrations → GitHub**
- Check GitHub's authorized apps in your account settings
- Verify the repository hasn't been renamed or moved

## Related

- [linear-setup.md](linear-setup.md) - Initial Linear configuration
- [../workflows/pr-opened-linear.md](../workflows/pr-opened-linear.md) - Custom workflow (fallback)
- [../workflows/pr-merge-linear.md](../workflows/pr-merge-linear.md) - Custom workflow (fallback)
