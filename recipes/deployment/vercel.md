# Vercel Deployment

Deploy frontend applications, full-stack Next.js apps, and serverless functions to Vercel's global edge network.

## When to Use Vercel

Use Vercel when you need:
- Zero-config deployments for Next.js, Vite, React, Vue, etc.
- Automatic preview deployments for every PR
- Global CDN with edge caching
- Serverless functions (Node.js, Go, Python, Ruby)
- Edge functions for low-latency compute

## Prerequisites

- Node.js 18+ installed
- Vercel account ([vercel.com](https://vercel.com))
- Vercel CLI installed

## Setup

### 1. Install Vercel CLI

```bash
npm install -g vercel
```

### 2. Authenticate

```bash
vercel login
```

### 3. Run Setup Wizard

```bash
bin/vibe setup --wizard vercel
```

Or link manually:

```bash
vercel link
```

### 4. Verify Setup

```bash
bin/vibe doctor
# Should show: [PASS] Vercel: CLI authenticated
```

## Project Configuration

### vercel.json

Basic configuration for most projects:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "nextjs"
}
```

### Framework-Specific Settings

**Next.js** (auto-detected):
```json
{
  "framework": "nextjs"
}
```

**Vite/React**:
```json
{
  "framework": "vite",
  "outputDirectory": "dist"
}
```

**Static Site**:
```json
{
  "outputDirectory": "public"
}
```

## Environment Variables

### Managing Environments

Vercel has three environments:
- **Production** - Live site (main/master branch)
- **Preview** - PR and branch deploys
- **Development** - Local development

### Setting Variables

```bash
# Via CLI
vercel env add DATABASE_URL production
vercel env add DATABASE_URL preview
vercel env add DATABASE_URL development

# Pull to local
vercel env pull .env.local
```

### Using the Secrets Provider

The boilerplate includes a Vercel secrets provider:

```python
from lib.vibe.secrets.providers.vercel import VercelSecretsProvider

provider = VercelSecretsProvider()

# List all env vars
secrets = provider.list_secrets("production")

# Set a secret
provider.set_secret("API_KEY", "value", "production")

# Sync from local file
provider.sync_from_local(".env.local", "preview")

# Pull from Vercel to local
provider.pull_to_local(".env.local", "development")
```

### Syncing with CLI

```bash
# Push local env to Vercel
bin/secrets sync --provider vercel --env production

# Pull from Vercel to local
vercel env pull .env.local
```

## Deployments

### Manual Deploy

```bash
# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### Automatic Deploys

Connect your GitHub repository in the Vercel dashboard:
1. Go to Project Settings > Git
2. Connect GitHub repository
3. Configure branch settings

Every push to `main` deploys to production. Every PR gets a preview URL.

### Preview Deployments

Preview deployments are created automatically for:
- Pull requests
- Non-production branches

Access preview URL from:
- PR comments (GitHub integration)
- Vercel dashboard
- CLI output after `vercel` command

## Serverless Functions

### API Routes (Next.js)

```typescript
// app/api/hello/route.ts
export async function GET() {
  return Response.json({ message: 'Hello!' });
}
```

### Standalone Functions

```typescript
// api/hello.ts
import type { VercelRequest, VercelResponse } from '@vercel/node';

export default function handler(req: VercelRequest, res: VercelResponse) {
  res.json({ message: 'Hello!' });
}
```

### Function Configuration

```json
// vercel.json
{
  "functions": {
    "api/**/*.ts": {
      "memory": 1024,
      "maxDuration": 30
    }
  }
}
```

## Edge Functions

For low-latency compute at the edge:

```typescript
// middleware.ts (Next.js)
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // Runs at the edge, globally
  return NextResponse.next();
}

export const config = {
  matcher: '/api/:path*',
};
```

## Custom Domains

### Adding a Domain

```bash
vercel domains add example.com
```

Or in dashboard: Project Settings > Domains

### DNS Configuration

Point your domain to Vercel:
- **A Record**: `76.76.21.21`
- **CNAME**: `cname.vercel-dns.com`

### SSL Certificates

Automatically provisioned and renewed by Vercel.

## Monorepo Support

### Root Configuration

```json
// vercel.json at root
{
  "projects": [
    { "src": "apps/web", "use": "@vercel/next" },
    { "src": "apps/api", "use": "@vercel/node" }
  ]
}
```

### Turborepo Integration

```json
// vercel.json
{
  "buildCommand": "cd ../.. && npx turbo run build --filter=web",
  "outputDirectory": "dist"
}
```

## Caching

### Build Cache

Vercel automatically caches:
- `node_modules`
- `.next/cache`
- Build outputs

### Edge Caching

```typescript
// app/api/data/route.ts
export async function GET() {
  return Response.json(data, {
    headers: {
      'Cache-Control': 's-maxage=3600, stale-while-revalidate',
    },
  });
}
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v25
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.VERCEL_ORG_ID }}
          vercel-project-id: ${{ secrets.VERCEL_PROJECT_ID }}
          vercel-args: '--prod'
```

### Required Secrets

Add to GitHub repository secrets:
- `VERCEL_TOKEN` - From Vercel account settings
- `VERCEL_ORG_ID` - From `.vercel/project.json` after linking
- `VERCEL_PROJECT_ID` - From `.vercel/project.json` after linking

## Troubleshooting

### Build Failures

```bash
# View build logs
vercel logs <deployment-url>

# Local build test
vercel build
```

### Environment Variable Issues

```bash
# List all env vars
vercel env ls

# Check specific environment
vercel env ls production
```

### Function Timeouts

Default timeout is 10s (Hobby) or 60s (Pro). Increase in `vercel.json`:

```json
{
  "functions": {
    "api/**": {
      "maxDuration": 30
    }
  }
}
```

### Cold Starts

Mitigate with:
- Edge functions (no cold starts)
- Smaller function bundles
- Keep functions warm with scheduled pings

## Related

- [Environment Syncing](../environments/env-syncing.md)
- [Secret Management](../security/secret-management.md)
- [Next.js Setup](../frameworks/nextjs.md)
