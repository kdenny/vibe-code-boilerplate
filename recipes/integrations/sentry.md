# Sentry Integration

[Sentry](https://sentry.io) provides error monitoring and performance tracking for production applications. This recipe covers setting up Sentry with the vibe-code-boilerplate workflow.

## When to Use Sentry

Use Sentry when your application:
- Runs in production and needs error visibility
- Would benefit from stack traces and context on crashes
- Needs performance monitoring (slow pages, API calls)
- Wants release tracking tied to deployments

## Quick Setup

### 1. Get Your DSN

1. Sign up at [sentry.io](https://sentry.io)
2. Create a new project (select your framework)
3. Copy the DSN from the setup instructions

### 2. Configure Environment

```bash
# Add to .env.local (gitignored)
echo "SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx" >> .env.local

# Optional: For release tracking
echo "SENTRY_AUTH_TOKEN=sntrys_xxx" >> .env.local
echo "SENTRY_ORG=your-org" >> .env.local
echo "SENTRY_PROJECT=your-project" >> .env.local
```

### 3. Verify Setup

```bash
bin/vibe doctor
# Should show: ✓ Sentry: DSN configured
```

## Framework-Specific Setup

### Next.js

```bash
npm install @sentry/nextjs
npx @sentry/wizard@latest -i nextjs
```

This creates:
- `sentry.client.config.ts` - Client-side config
- `sentry.server.config.ts` - Server-side config
- `sentry.edge.config.ts` - Edge runtime config
- Updated `next.config.js` with Sentry webpack plugin

### Python (Flask/FastAPI/Django)

```bash
pip install sentry-sdk
```

```python
# In your app initialization
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    traces_sample_rate=0.1,  # Adjust based on traffic
    profiles_sample_rate=0.1,
)
```

### Node.js (Express/Fastify)

```bash
npm install @sentry/node
```

```javascript
const Sentry = require("@sentry/node");

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
});
```

## Release Tracking

Link Sentry releases to your Git commits and deployments:

### GitHub Actions Integration

Add to your deploy workflow:

```yaml
- name: Create Sentry Release
  uses: getsentry/action-release@v1
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: ${{ vars.SENTRY_ORG }}
    SENTRY_PROJECT: ${{ vars.SENTRY_PROJECT }}
  with:
    environment: production
    version: ${{ github.sha }}
```

### Source Maps (JavaScript)

For better stack traces, upload source maps:

```yaml
- name: Upload Source Maps
  run: |
    npx @sentry/cli releases files ${{ github.sha }} upload-sourcemaps ./dist
  env:
    SENTRY_AUTH_TOKEN: ${{ secrets.SENTRY_AUTH_TOKEN }}
    SENTRY_ORG: ${{ vars.SENTRY_ORG }}
    SENTRY_PROJECT: ${{ vars.SENTRY_PROJECT }}
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `SENTRY_DSN` | Yes | Data Source Name - project ingest URL |
| `SENTRY_AUTH_TOKEN` | For releases | API token for release management |
| `SENTRY_ORG` | For releases | Organization slug |
| `SENTRY_PROJECT` | For releases | Project slug |
| `SENTRY_ENVIRONMENT` | Optional | Environment name (production, staging) |

## Best Practices

### 1. Sample Rates

Don't capture 100% of transactions in production:

```javascript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,  // 10% of transactions
  profilesSampleRate: 0.1, // 10% of profiled transactions
});
```

### 2. Environment Separation

Use separate projects or environments:

```javascript
Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV, // development, staging, production
});
```

### 3. User Context

Add user context for better debugging:

```javascript
Sentry.setUser({
  id: user.id,
  email: user.email,
  // Don't include PII you don't need
});
```

### 4. Custom Tags

Tag errors for filtering:

```javascript
Sentry.setTag("feature", "checkout");
Sentry.setTag("plan", user.plan);
```

### 5. Breadcrumbs

Add custom breadcrumbs for context:

```javascript
Sentry.addBreadcrumb({
  category: "auth",
  message: "User logged in",
  level: "info",
});
```

## Troubleshooting

### Errors Not Appearing

1. Verify DSN is correct and not expired
2. Check browser console for Sentry initialization errors
3. Verify the error isn't being caught and swallowed
4. Check Sentry's ingest status page

### Source Maps Not Working

1. Verify source maps are being generated
2. Check upload succeeded in CI logs
3. Verify release version matches between upload and runtime
4. Check artifact bundle in Sentry UI

### High Volume Warnings

1. Adjust sample rates
2. Use `beforeSend` to filter noise
3. Set up alert rules instead of watching all errors

## Integration with Vibe Workflow

### PR-Based Releases

When a PR is merged, the release is created:

```yaml
# In pr-merged workflow or deploy workflow
- name: Notify Sentry of Deploy
  run: |
    curl -X POST "https://sentry.io/api/0/organizations/$SENTRY_ORG/releases/" \
      -H "Authorization: Bearer $SENTRY_AUTH_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "version": "${{ github.sha }}",
        "projects": ["${{ vars.SENTRY_PROJECT }}"],
        "refs": [{"repository": "${{ github.repository }}", "commit": "${{ github.sha }}"}]
      }'
```

### Linking Errors to Tickets

When Sentry captures an error, create a Linear ticket:

1. Go to Sentry → Settings → Integrations → Linear
2. Enable the integration
3. Configure auto-issue creation rules

## Related

- [secret-management.md](../security/secret-management.md) - Handling API keys
- [deployment](../deployment/) - Fly.io and Vercel deployment guides
