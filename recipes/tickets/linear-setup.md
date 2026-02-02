# Linear Setup

## When to Use This Recipe

Use this recipe when you need to:
- Set up Linear as your ticket tracking system
- Configure Linear for vibe boilerplate integration
- Set up labels and workflow states

## Prerequisites

- Linear account (linear.app)
- Workspace admin access (for API keys and label setup)

## Step 1: Get API Key

1. Go to Linear Settings (click avatar → Settings)
2. Navigate to **API** section
3. Click **Create Key**
4. Name it something like "Vibe Integration"
5. Copy the key (starts with `lin_api_`)

Store it securely:
```bash
# In .env.local (never commit)
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxx
```

## Step 2: Find Your Team ID

Team ID is needed for creating tickets in the right place.

### Via URL
1. Go to your team's page in Linear
2. The URL looks like: `https://linear.app/yourworkspace/team/ENG/...`
3. Note: You need the actual UUID, not the short code

### Via API
```bash
# Using the vibe CLI (after setup)
bin/ticket list

# Or via Linear API directly
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ teams { nodes { id name } } }"}'
```

## Step 3: Configure Vibe

Run the setup wizard:
```bash
bin/vibe setup
```

Or manually edit `.vibe/config.json`:
```json
{
  "tracker": {
    "type": "linear",
    "config": {
      "team_id": "your-team-uuid",
      "workspace": "your-workspace-slug"
    }
  }
}
```

## Step 4: Set Up Labels

Create these labels in Linear to match the vibe conventions:

### Type Labels
- **Bug** - Something isn't working
- **Feature** - New functionality
- **Chore** - Maintenance, cleanup
- **Refactor** - Code improvement, no behavior change

### Risk Labels
- **Low Risk** - Minimal scope, easy to revert
- **Medium Risk** - Moderate scope, needs testing
- **High Risk** - Large scope, critical path

### Area Labels
- **Frontend** - UI/UX changes
- **Backend** - Server/API changes
- **Infra** - Infrastructure, DevOps
- **Docs** - Documentation

### Special Labels
- **HUMAN** - Requires human decision/action
- **Milestone** - Part of a larger feature
- **Blocked** - Waiting on external dependency

## Step 5: Configure Workflow States

Recommended Linear workflow states:

```
Backlog → Todo → In Progress → In Review → Done
                                   ↓
                              Cancelled
```

Map these in your process:
- **Backlog**: Prioritized but not started
- **Todo**: Ready to be picked up
- **In Progress**: Being worked on
- **In Review**: PR open, awaiting review
- **Done**: Merged and deployed
- **Cancelled**: Won't do

## Step 6: GitHub Integration

Enable Linear's GitHub integration for:
- Automatic ticket linking from branch names
- PR status updates on ticket
- Auto-close tickets on merge

In Linear:
1. Settings → Integrations → GitHub
2. Connect your GitHub account
3. Select repositories

## Usage

### Create Ticket
```bash
bin/ticket create "Add user authentication" --label Feature
```

### List Tickets
```bash
bin/ticket list --status "In Progress"
```

### Start Working on Ticket
```bash
bin/vibe do ENG-123
# Creates worktree with branch ENG-123-*
```

## Troubleshooting

### "Unauthorized" Error
- Check LINEAR_API_KEY is set in environment
- Verify key is valid (not expired)
- Ensure key has correct permissions

### "Team not found" Error
- Verify team_id is correct UUID
- Check you have access to the team
- Try fetching teams list to confirm

### Ticket Not Linking
- Ensure branch name includes ticket ID (e.g., `ENG-123`)
- Check GitHub integration is enabled in Linear
- Verify PR title or body contains ticket reference

## Extension Points

- Add custom fields for your workflow
- Configure automated status transitions
- Set up Slack notifications
