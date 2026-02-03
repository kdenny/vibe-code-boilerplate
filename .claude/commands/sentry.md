---
description: Configure and manage Sentry error monitoring
allowed-tools: Bash, Read, Write
---

# /sentry - Sentry Error Monitoring

Configure Sentry for error tracking, performance monitoring, and release management.

## Subcommands

### setup
Initialize Sentry in the project.

```
/sentry setup              # Interactive setup
/sentry setup nextjs       # Next.js setup
/sentry setup python       # Python setup
/sentry setup node         # Node.js setup
```

### release
Manage Sentry releases.

```
/sentry release create     # Create release for current commit
/sentry release deploy     # Mark release as deployed
```

### sourcemaps
Upload source maps for JavaScript projects.

```
/sentry sourcemaps         # Upload source maps from dist/
/sentry sourcemaps ./build # Upload from custom path
```

### status
Check Sentry configuration status.

```
/sentry status             # Show DSN, project, and env config
```

### test
Send a test event to verify setup.

```
/sentry test               # Send test error
```

## Instructions

When the user invokes `/sentry`:

### For `setup`:

1. Check if Sentry CLI is installed:

```bash
which sentry-cli
```

If not installed, guide installation:
```bash
# macOS
brew install getsentry/tools/sentry-cli

# npm
npm install -g @sentry/cli
```

2. Check for existing configuration:
   - Look for `SENTRY_DSN` in `.env.local` or `.env`
   - Check for `sentry.*.config.ts` files (Next.js)
   - Check for `sentry_sdk.init()` calls (Python)

3. For framework-specific setup:

**Next.js:**
```bash
npx @sentry/wizard@latest -i nextjs
```

This creates:
- `sentry.client.config.ts`
- `sentry.server.config.ts`
- `sentry.edge.config.ts`
- Updates `next.config.js`

**Python:**
```bash
pip install sentry-sdk
```

Create initialization in app entry:
```python
import sentry_sdk

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    traces_sample_rate=0.1,
)
```

**Node.js:**
```bash
npm install @sentry/node
```

Create initialization:
```javascript
const Sentry = require("@sentry/node");

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 0.1,
});
```

4. Prompt for DSN if not configured:
   - Guide user to sentry.io to create project
   - Help add `SENTRY_DSN` to `.env.local`

### For `release create`:

1. Check required env vars:
   - `SENTRY_AUTH_TOKEN`
   - `SENTRY_ORG`
   - `SENTRY_PROJECT`

2. Create release:
```bash
sentry-cli releases new $(git rev-parse HEAD)
sentry-cli releases set-commits $(git rev-parse HEAD) --auto
```

### For `release deploy`:

```bash
sentry-cli releases deploys $(git rev-parse HEAD) new -e production
```

### For `sourcemaps`:

1. Verify build artifacts exist
2. Upload source maps:

```bash
sentry-cli releases files $(git rev-parse HEAD) upload-sourcemaps ./dist
```

### For `status`:

1. Check environment variables:
```bash
echo "SENTRY_DSN: ${SENTRY_DSN:+configured}"
echo "SENTRY_AUTH_TOKEN: ${SENTRY_AUTH_TOKEN:+configured}"
echo "SENTRY_ORG: ${SENTRY_ORG:-not set}"
echo "SENTRY_PROJECT: ${SENTRY_PROJECT:-not set}"
```

2. Check for framework configurations:
   - Next.js: `sentry.*.config.ts`
   - Python: `sentry_sdk.init` in codebase
   - Node.js: `@sentry/node` in package.json

### For `test`:

1. Verify DSN is configured
2. Send test event:

**JavaScript:**
```javascript
Sentry.captureException(new Error("Test error from /sentry test"));
```

**Python:**
```python
sentry_sdk.capture_message("Test message from /sentry test")
```

3. Provide link to Sentry dashboard to verify

## Example Session

```
User: /sentry setup nextjs

Claude: I'll set up Sentry for your Next.js project.

Step 1: Checking Sentry CLI...
✓ sentry-cli is installed

Step 2: Running Sentry wizard for Next.js...

[Runs: npx @sentry/wizard@latest -i nextjs]

✓ Created sentry.client.config.ts
✓ Created sentry.server.config.ts
✓ Updated next.config.js

Step 3: Environment configuration...

Add to .env.local:
  SENTRY_DSN=<your-dsn>
  SENTRY_AUTH_TOKEN=<for-releases>
  SENTRY_ORG=<your-org>
  SENTRY_PROJECT=<your-project>

Get your DSN from: https://sentry.io > Project > Settings > Client Keys

Your Sentry setup is complete! Run `/sentry test` to verify.
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SENTRY_DSN` | Yes | Data Source Name for error ingestion |
| `SENTRY_AUTH_TOKEN` | For releases | API token for release management |
| `SENTRY_ORG` | For releases | Organization slug |
| `SENTRY_PROJECT` | For releases | Project slug |
| `SENTRY_ENVIRONMENT` | Optional | Environment name (production, staging) |

## Common Issues

| Issue | Solution |
|-------|----------|
| CLI not installed | Install: `brew install getsentry/tools/sentry-cli` |
| DSN not set | Get from Sentry > Project > Settings > Client Keys |
| Auth token invalid | Create new token at sentry.io > Settings > Auth Tokens |
| Source maps not linking | Verify release version matches between upload and runtime |
| Events not appearing | Check browser console for Sentry errors, verify DSN |

## Related

- `recipes/integrations/sentry.md` - Full Sentry documentation
- `recipes/security/secret-management.md` - Managing API keys
