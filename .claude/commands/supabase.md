---
description: Manage Supabase database, auth, and local development
allowed-tools: Bash, Read, Write
---

# /supabase - Supabase Management

Manage Supabase database migrations, types generation, and local development.

## Subcommands

### start
Start local Supabase development environment.

```
/supabase start            # Start all services
/supabase start db         # Start only database
```

### stop
Stop local Supabase.

```
/supabase stop             # Stop all services
```

### migrate
Manage database migrations.

```
/supabase migrate new <name>   # Create new migration
/supabase migrate up           # Apply migrations (local)
/supabase migrate push         # Push to remote
```

### types
Generate TypeScript types.

```
/supabase types            # Generate from local
/supabase types --remote   # Generate from remote project
```

### db
Database operations.

```
/supabase db reset         # Reset local database
/supabase db diff          # Show schema diff
/supabase db dump          # Dump schema
```

### status
Check Supabase status.

```
/supabase status           # Local and project status
```

## Instructions

When the user invokes `/supabase`:

### For `start`:

1. Check if Supabase CLI is installed
2. Check if project is initialized (`supabase/config.toml`)
3. Start local services:

```bash
supabase start
```

4. Report URLs and keys for local development

### For `stop`:

```bash
supabase stop
```

### For `migrate new`:

1. Create migration file:

```bash
supabase migration new <name>
```

2. Report file path for editing
3. Remind about RLS policies

### For `migrate up` / `migrate push`:

```bash
# Local
supabase db reset  # Applies all migrations

# Remote
supabase db push
```

### For `types`:

```bash
# From local
supabase gen types typescript --local > types/supabase.ts

# From remote
supabase gen types typescript --project-id <id> > types/supabase.ts
```

Report the output path and remind to import in client setup.

### For `db reset`:

1. Warn that this destroys local data
2. Run reset:

```bash
supabase db reset
```

### For `status`:

1. Check local status: `supabase status`
2. Check if linked to remote project
3. Report connection URLs and status

## Example Session

```
User: /supabase start

Claude: I'll start local Supabase.

Starting Supabase local development...

✓ Supabase started!

Local URLs:
  API URL:      http://localhost:54321
  GraphQL URL:  http://localhost:54321/graphql/v1
  Database URL: postgresql://postgres:postgres@localhost:54322/postgres
  Studio URL:   http://localhost:54323

Keys (for .env.local):
  SUPABASE_URL=http://localhost:54321
  SUPABASE_ANON_KEY=eyJ...
  SUPABASE_SERVICE_ROLE_KEY=eyJ...
```

## Common Issues

| Issue | Solution |
|-------|----------|
| CLI not installed | Install: `brew install supabase/tap/supabase` |
| Not initialized | Run `supabase init` |
| Port conflict | Stop other services on 54321-54323 |
| Docker not running | Start Docker Desktop |
| Migration failed | Check SQL syntax, run `supabase db reset` |

## Related

- `recipes/databases/supabase.md` - Full Supabase documentation
- `recipes/security/secret-management.md` - Managing API keys
