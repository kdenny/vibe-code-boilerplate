# Neon Integration

[Neon](https://neon.tech) is a serverless Postgres platform with instant branching, making it ideal for development workflows that use git worktrees.

## When to Use Neon

Use Neon when your application:
- Needs a Postgres database
- Would benefit from database branching (one DB branch per feature branch)
- Wants instant provisioning for CI/CD and preview environments
- Prefers serverless scaling over managing database servers

## Quick Setup

### 1. Create a Neon Account

1. Sign up at [neon.tech](https://neon.tech)
2. Create a new project
3. Copy the connection string from the dashboard

### 2. Configure Environment

```bash
# Add to .env.local (gitignored)
echo "DATABASE_URL=postgres://user:pass@ep-xxx.us-east-2.aws.neon.tech/neondb" >> .env.local

# Optional: For database branching via API
echo "NEON_API_KEY=neon_xxx" >> .env.local
```

### 3. Verify Setup

```bash
bin/vibe doctor
# Should show: ✓ Neon: DATABASE_URL configured
```

## Connection String Format

Neon provides connection strings in this format:

```
postgres://[user]:[password]@[host]/[database]?sslmode=require
```

For pooled connections (recommended for serverless):
```
postgres://[user]:[password]@[host]/[database]?sslmode=require&pgbouncer=true
```

## Database Branching

Neon's killer feature is database branching - create isolated database copies instantly.

### Manual Branching

```bash
# Install Neon CLI
brew install neon

# Authenticate
neonctl auth

# Create a branch from main
neonctl branches create --name feature-123

# Get the connection string for the branch
neonctl connection-string --branch feature-123
```

### Automated Branching (with Worktrees)

You can script database branch creation when creating a worktree:

```bash
# In a post-worktree hook or wrapper script
BRANCH_NAME="$1"
neonctl branches create --name "$BRANCH_NAME" 2>/dev/null || true
CONNECTION_STRING=$(neonctl connection-string --branch "$BRANCH_NAME")
echo "DATABASE_URL=$CONNECTION_STRING" >> .env.local
```

### Branch Lifecycle

| Git Action | Database Action |
|------------|-----------------|
| Create feature branch | Create Neon branch |
| Work on feature | Use branch database |
| Merge PR | Delete Neon branch (optional) |
| Main branch | Use main Neon branch |

## Framework Integration

### Prisma

```bash
npm install prisma @prisma/client
npx prisma init
```

In `prisma/schema.prisma`:
```prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

```bash
# Generate client
npx prisma generate

# Push schema changes
npx prisma db push

# Run migrations
npx prisma migrate dev
```

### Drizzle

```bash
npm install drizzle-orm postgres
npm install -D drizzle-kit
```

```typescript
// db/index.ts
import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';

const client = postgres(process.env.DATABASE_URL!);
export const db = drizzle(client);
```

### Raw SQL (Node.js)

```bash
npm install postgres
```

```typescript
import postgres from 'postgres';

const sql = postgres(process.env.DATABASE_URL!);

const users = await sql`SELECT * FROM users WHERE id = ${userId}`;
```

### Python (SQLAlchemy)

```bash
pip install sqlalchemy psycopg2-binary
```

```python
from sqlalchemy import create_engine

engine = create_engine(os.environ["DATABASE_URL"])
```

## CI/CD Integration

### Preview Environments

Create a database branch for each PR:

```yaml
# .github/workflows/preview.yml
- name: Create Neon Branch
  id: neon
  run: |
    BRANCH_NAME="pr-${{ github.event.pull_request.number }}"
    neonctl branches create --name "$BRANCH_NAME" 2>/dev/null || true
    echo "connection_string=$(neonctl connection-string --branch $BRANCH_NAME)" >> $GITHUB_OUTPUT
  env:
    NEON_API_KEY: ${{ secrets.NEON_API_KEY }}

- name: Run Migrations
  run: npx prisma migrate deploy
  env:
    DATABASE_URL: ${{ steps.neon.outputs.connection_string }}
```

### Cleanup on PR Close

```yaml
# .github/workflows/preview-cleanup.yml
on:
  pull_request:
    types: [closed]

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - name: Delete Neon Branch
        run: |
          neonctl branches delete "pr-${{ github.event.pull_request.number }}" --force
        env:
          NEON_API_KEY: ${{ secrets.NEON_API_KEY }}
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Postgres connection string |
| `NEON_API_KEY` | For branching | API key for Neon management |
| `NEON_PROJECT_ID` | Optional | Project ID for CLI operations |

## Best Practices

### 1. Use Connection Pooling

For serverless environments, use pooled connections:

```
DATABASE_URL=postgres://...?pgbouncer=true&connect_timeout=15
```

### 2. Branch Naming Convention

Match database branches to git branches:

```
Git: feature/PROJ-123-add-auth
Neon: proj-123-add-auth (lowercase, no slashes)
```

### 3. Seed Data

Create a seed script for development branches:

```bash
# seed.sql or seed.ts
npx prisma db seed
```

### 4. Schema Migrations

Always use migrations, not `db push` in production:

```bash
# Development
npx prisma migrate dev --name add_users_table

# Production/CI
npx prisma migrate deploy
```

### 5. Connection Timeouts

Set appropriate timeouts for serverless:

```typescript
const sql = postgres(process.env.DATABASE_URL!, {
  connect_timeout: 15,
  idle_timeout: 20,
  max_lifetime: 60 * 30,
});
```

## Troubleshooting

### Connection Timeout

1. Check if using pooled connection string
2. Verify IP allowlist settings (if enabled)
3. Check Neon dashboard for branch status

### Branch Not Found

1. Verify branch name matches exactly
2. Check if branch was auto-suspended (wake it up)
3. Verify API key has correct permissions

### Slow Queries

1. Enable connection pooling
2. Check for missing indexes
3. Review Neon's query insights dashboard

## Comparison with Supabase

| Feature | Neon | Supabase |
|---------|------|----------|
| Core | Serverless Postgres | Postgres + extras |
| Branching | Native, instant | Via Supabase Branching |
| Auth | BYO | Built-in |
| Storage | BYO | Built-in |
| Realtime | BYO | Built-in |
| Best for | Pure database needs | Full backend platform |

## Related

- [supabase.md](../databases/supabase.md) - Supabase integration
- [secret-management.md](../security/secret-management.md) - Handling credentials
