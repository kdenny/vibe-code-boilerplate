---
description: Deploy and manage Fly.io applications
allowed-tools: Bash, Read, Write
---

# /fly - Fly.io Deployment Management

Manage Fly.io deployments, secrets, scaling, and monitoring.

## Subcommands

### deploy
Deploy to Fly.io.

```
/fly deploy                 # Deploy current app
/fly deploy --no-cache      # Deploy without build cache
```

### secrets
Manage application secrets.

```
/fly secrets list           # List secret names
/fly secrets sync           # Sync .env.local to Fly.io
/fly secrets set KEY=value  # Set a secret
```

### logs
View application logs.

```
/fly logs                   # Stream logs
/fly logs --no-tail         # View recent logs
```

### status
Check application status.

```
/fly status                 # App and machine status
```

### ssh
SSH into running machine.

```
/fly ssh                    # Interactive shell
/fly ssh "command"          # Run command
```

## Instructions

When the user invokes `/fly`:

### For `deploy`:

1. Check if Fly CLI is installed and authenticated
2. Check if `fly.toml` exists
3. Run deployment:

```bash
# Standard deploy
fly deploy

# Without cache
fly deploy --no-cache
```

4. Report deployment status and URL

### For `secrets list`:

1. Run `fly secrets list`
2. Display secret names (values are hidden by Fly.io)

### For `secrets sync`:

1. Check if `.env.local` or `.env.production` exists
2. Use the Fly secrets provider:

```python
from lib.vibe.secrets.providers.fly import FlySecretsProvider

provider = FlySecretsProvider(app_name="app-name-from-fly-toml")
results = provider.sync_from_local(".env.local", "production")
provider.deploy()  # Deploy the staged secrets
```

3. Report success/failure for each secret

### For `secrets set`:

1. Parse KEY=value from arguments
2. Run `fly secrets set KEY=value`
3. Report success

### For `logs`:

```bash
# Stream logs
fly logs

# Recent logs only
fly logs --no-tail
```

### For `status`:

1. Run `fly status` for app overview
2. Run `fly machine list` for machine details
3. Report app URL, machine status, regions

### For `ssh`:

```bash
# Interactive
fly ssh console

# Command
fly ssh console -C "command"
```

## Example Session

```
User: /fly deploy

Claude: I'll deploy to Fly.io.

Checking prerequisites...
✓ Fly CLI authenticated
✓ fly.toml found (app: my-app)

Deploying...

✓ Deployment complete!

App URL: https://my-app.fly.dev
Machines: 2 running in iad
Version: v42
```

## Common Issues

| Issue | Solution |
|-------|----------|
| Not authenticated | Run `fly auth login` |
| No fly.toml | Run `fly launch` to create |
| Build failed | Check Dockerfile and logs |
| Health check failing | Verify /health endpoint |
| Out of memory | Increase `memory_mb` in fly.toml |

## Related

- `recipes/deployment/fly-io.md` - Full Fly.io documentation
- `recipes/security/secret-management.md` - Secrets handling
