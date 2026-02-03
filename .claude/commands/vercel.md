---
description: Deploy and manage Vercel projects
allowed-tools: Bash, Read, Write
---

# /vercel - Vercel Deployment Management

Manage Vercel deployments, environment variables, and project configuration.

## Subcommands

### deploy
Deploy to Vercel.

```
/vercel deploy              # Deploy to preview
/vercel deploy --prod       # Deploy to production
```

### env
Manage environment variables.

```
/vercel env list            # List all env vars
/vercel env pull            # Pull env vars to .env.local
/vercel env sync            # Sync .env.local to Vercel
```

### logs
View deployment logs.

```
/vercel logs                # Latest deployment logs
/vercel logs <url>          # Specific deployment logs
```

### status
Check project status.

```
/vercel status              # Current project status
```

## Instructions

When the user invokes `/vercel`:

### For `deploy`:

1. Check if Vercel CLI is installed and authenticated
2. Check if project is linked (`vercel link`)
3. Run deployment:

```bash
# Preview deployment
vercel

# Production deployment
vercel --prod
```

4. Report deployment URL and status

### For `env list`:

1. Run `vercel env ls` to list all environment variables
2. Group by environment (production, preview, development)
3. Report which variables are set in each environment

### For `env pull`:

1. Run `vercel env pull .env.local`
2. Report which variables were pulled
3. Remind user that `.env.local` is gitignored

### For `env sync`:

1. Check if `.env.local` exists
2. Parse the file for variables to sync
3. Use the Vercel secrets provider:

```python
from lib.vibe.secrets.providers.vercel import VercelSecretsProvider

provider = VercelSecretsProvider()
results = provider.sync_from_local(".env.local", "preview")
```

4. Report success/failure for each variable

### For `logs`:

1. Get latest deployment or use provided URL
2. Run `vercel logs <url>`
3. Display recent log entries

### For `status`:

1. Check CLI authentication: `vercel whoami`
2. Check project link status
3. List recent deployments: `vercel ls`
4. Report current production URL

## Example Session

```
User: /vercel deploy --prod

Claude: I'll deploy to Vercel production.

Checking prerequisites...
✓ Vercel CLI authenticated as user@example.com
✓ Project linked: my-app

Deploying to production...

✓ Deployment complete!

Production URL: https://my-app.vercel.app
Deployment URL: https://my-app-abc123.vercel.app

Deployment took 45s
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Not authenticated | Run `vercel login` |
| Project not linked | Run `vercel link` |
| Build failed | Check `vercel logs` for errors |
| Env var not found | Verify with `vercel env ls` |

## Related

- `recipes/deployment/vercel.md` - Full Vercel documentation
- `recipes/security/secret-management.md` - Secrets handling
