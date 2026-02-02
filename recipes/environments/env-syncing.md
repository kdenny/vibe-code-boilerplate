# Environment Variable Syncing

## When to Use This Recipe

Use this recipe when you need to:
- Keep environment variables consistent across local, CI, and production
- Add new environment variables without breaking deployments
- Audit environment variable usage across environments

## The Environment Chain

```
.env.example     →     .env.local      →     CI Secrets      →     Production
(template)            (local dev)           (GitHub)              (Platform)
```

## Adding a New Environment Variable

### Step 1: Add to .env.example
```bash
# .env.example
# Description of what this variable does
NEW_API_KEY=your_key_here
```

### Step 2: Add locally
```bash
# .env.local (not committed)
NEW_API_KEY=actual_dev_key
```

### Step 3: Add to CI
```bash
# Via GitHub CLI
gh secret set NEW_API_KEY --body "ci_key_value"

# Or via GitHub UI: Settings → Secrets → Actions
```

### Step 4: Add to production
Depends on your platform:

```bash
# Vercel
vercel env add NEW_API_KEY

# Fly.io
fly secrets set NEW_API_KEY=production_value

# Railway
railway variables set NEW_API_KEY=production_value
```

## Syncing Workflow

### Using vibe CLI
```bash
# Preview what would be synced
bin/secrets sync .env.local --provider github --dry-run

# Sync to GitHub Actions secrets
bin/secrets sync .env.local --provider github --environment repository

# Sync to Vercel (when implemented)
bin/secrets sync .env.local --provider vercel --environment production
```

### Manual Sync Checklist
When adding new env vars, update:
- [ ] `.env.example` (with description)
- [ ] `.env.local` (with real value)
- [ ] GitHub Actions secrets
- [ ] Production platform secrets
- [ ] Documentation (if API key or external service)

## Environment-Specific Values

Some values differ per environment:

| Variable | Local | CI | Staging | Production |
|----------|-------|-----|---------|------------|
| `DATABASE_URL` | localhost | test-db | staging-db | prod-db |
| `LOG_LEVEL` | debug | info | info | warn |
| `API_URL` | localhost:3000 | mock | staging.app.com | app.com |

## Validating Environments

### Startup Validation
```python
# In your app's startup
required_vars = ['DATABASE_URL', 'API_KEY', 'SECRET_KEY']
missing = [v for v in required_vars if not os.environ.get(v)]
if missing:
    raise EnvironmentError(f"Missing required env vars: {missing}")
```

### CI Validation
```yaml
# In GitHub Actions
- name: Validate environment
  run: |
    if [ -z "$DATABASE_URL" ]; then
      echo "Missing DATABASE_URL"
      exit 1
    fi
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

## Troubleshooting

### "Variable works locally but not in CI"
1. Check if secret is set: `gh secret list`
2. Check workflow uses secret: `${{ secrets.VAR_NAME }}`
3. Check secret name matches exactly (case-sensitive)

### "Variable works in CI but not production"
1. Verify platform has the variable set
2. Check for typos in variable name
3. Verify app is reading from correct source

## Best Practices

1. **Always update .env.example** when adding new vars
2. **Use descriptive comments** in .env.example
3. **Validate on startup** - fail fast if vars missing
4. **Use environment-specific secrets** - don't share across prod/staging
5. **Audit regularly** - remove unused variables

## Extension Points

- Add custom validation rules
- Implement secret rotation workflows
- Set up environment diff checking
