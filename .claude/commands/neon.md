---
description: Manage Neon serverless Postgres databases and branches
allowed-tools: Bash, Read, Write
---

# /neon - Neon Database Management

Manage Neon serverless Postgres databases with instant branching for development workflows.

## Subcommands

### setup
Initialize Neon in the project.

```
/neon setup                # Interactive setup
```

### branch
Manage database branches.

```
/neon branch create <name> # Create branch from main
/neon branch list          # List all branches
/neon branch delete <name> # Delete a branch
/neon branch switch <name> # Get connection string for branch
```

### connection
Get connection strings.

```
/neon connection           # Get main branch connection string
/neon connection <branch>  # Get specific branch connection string
/neon connection --pooled  # Get pooled connection (recommended for serverless)
```

### status
Check Neon configuration status.

```
/neon status               # Show project, branches, and env config
```

## Instructions

When the user invokes `/neon`:

### For `setup`:

1. Check if Neon CLI is installed:

```bash
which neonctl
```

If not installed, guide installation:
```bash
# macOS
brew install neon

# npm
npm install -g neonctl
```

2. Check authentication:

```bash
neonctl auth status
```

If not authenticated:
```bash
neonctl auth
```

3. Check for existing configuration:
   - Look for `DATABASE_URL` in `.env.local` or `.env`
   - Look for `NEON_API_KEY` for branching capabilities

4. Prompt for project linking:
   - List available projects: `neonctl projects list`
   - Set project context: `neonctl set-context --project-id <id>`

5. Help configure environment variables:
   - Add `DATABASE_URL` to `.env.local`
   - Add `NEON_API_KEY` for branching (optional)

### For `branch create`:

1. Verify CLI is authenticated
2. Create branch from main:

```bash
neonctl branches create --name <branch-name>
```

3. Get and display connection string:

```bash
neonctl connection-string --branch <branch-name>
```

4. Optionally update `.env.local` with branch connection string

### For `branch list`:

```bash
neonctl branches list
```

Display as formatted table with:
- Branch name
- Created date
- Status (active/idle)

### For `branch delete`:

1. Confirm deletion (warn about data loss)
2. Delete branch:

```bash
neonctl branches delete <branch-name> --force
```

### For `branch switch`:

1. Get connection string for branch:

```bash
neonctl connection-string --branch <branch-name>
```

2. Offer to update `.env.local`:
   - Backup current `DATABASE_URL`
   - Set new `DATABASE_URL` for branch

### For `connection`:

```bash
# Main branch
neonctl connection-string

# Specific branch
neonctl connection-string --branch <name>

# Pooled (add ?pgbouncer=true)
neonctl connection-string --pooled
```

Recommend pooled connections for serverless environments (Vercel, Netlify).

### For `status`:

1. Check CLI installation and auth
2. Show current project context:

```bash
neonctl projects list --context
```

3. List branches:

```bash
neonctl branches list
```

4. Check environment variables:
   - `DATABASE_URL` configured?
   - `NEON_API_KEY` configured?

## Example Session

```
User: /neon branch create feature-123

Claude: I'll create a Neon database branch for feature-123.

Creating branch...
✓ Branch 'feature-123' created from 'main'

Connection string:
postgres://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

Add to .env.local:
DATABASE_URL=postgres://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require

For pooled connections (recommended for serverless):
DATABASE_URL=postgres://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require&pgbouncer=true

Branch is ready! Don't forget to run migrations if needed.
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Postgres connection string |
| `NEON_API_KEY` | For branching | API key for branch management |
| `NEON_PROJECT_ID` | Optional | Project ID for CLI operations |

## Common Issues

| Issue | Solution |
|-------|----------|
| CLI not installed | Install: `brew install neon` or `npm install -g neonctl` |
| Not authenticated | Run: `neonctl auth` |
| Branch not found | Check name with `neonctl branches list` |
| Connection timeout | Use pooled connection with `?pgbouncer=true` |
| Branch suspended | Access it to wake up (auto-resumes on connection) |

## Workflow Integration

### With Git Worktrees

When creating a worktree for a ticket, create a matching database branch:

```bash
# Create worktree
bin/vibe do PROJ-123

# Create matching database branch
neonctl branches create --name proj-123
CONNECTION=$(neonctl connection-string --branch proj-123)

# Add to worktree's .env.local
echo "DATABASE_URL=$CONNECTION" >> ../project-worktrees/PROJ-123/.env.local
```

### PR Preview Environments

Create database branches for PR previews in CI:

```yaml
- name: Create Neon Branch
  run: |
    neonctl branches create --name "pr-${{ github.event.pull_request.number }}" || true
    echo "DATABASE_URL=$(neonctl connection-string --branch pr-${{ github.event.pull_request.number }})" >> $GITHUB_ENV
```

## Related

- `recipes/integrations/neon.md` - Full Neon documentation
- `recipes/security/secret-management.md` - Managing credentials
