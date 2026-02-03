# Fly.io Deployment

Deploy containerized applications globally with Fly.io's edge infrastructure. Run servers close to your users with automatic SSL, scaling, and managed services.

## When to Use Fly.io

Use Fly.io when you need:
- Full-stack applications with server-side logic
- Global distribution with low latency
- Persistent storage (volumes, databases)
- Long-running processes or WebSockets
- Docker-based deployments
- Managed Postgres, Redis, or other services

## Prerequisites

- Docker installed (for local builds)
- Fly.io account ([fly.io](https://fly.io))
- Fly CLI installed

## Setup

### 1. Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### 2. Authenticate

```bash
fly auth login
```

### 3. Run Setup Wizard

```bash
bin/vibe setup --wizard fly
```

Or launch manually:

```bash
fly launch
```

### 4. Verify Setup

```bash
bin/vibe doctor
# Should show: [PASS] Fly.io: CLI authenticated
```

## Project Configuration

### fly.toml

Basic configuration:

```toml
app = "my-app"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[http_service]
  internal_port = 8080
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
```

### Dockerfile

Example for a Python app:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Example for a Node.js app:

```dockerfile
FROM node:20-slim

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000
CMD ["node", "server.js"]
```

## Secrets Management

### Setting Secrets

```bash
# Single secret
fly secrets set DATABASE_URL="postgres://..."

# Multiple secrets
fly secrets set API_KEY="xxx" SECRET_KEY="yyy"

# From file
fly secrets import < .env.production
```

### Using the Secrets Provider

The boilerplate includes a Fly.io secrets provider:

```python
from lib.vibe.secrets.providers.fly import FlySecretsProvider

provider = FlySecretsProvider(app_name="my-app")

# List secrets (names only - values are hidden)
secrets = provider.list_secrets()

# Set a secret (staged, not deployed)
provider.set_secret("API_KEY", "value", "production")

# Sync from local file
provider.sync_from_local(".env.production", "production")

# Deploy staged secrets
provider.deploy()
```

### Viewing Secrets

```bash
# List secret names
fly secrets list

# Note: Values are never shown for security
```

## Deployments

### Manual Deploy

```bash
# Deploy current directory
fly deploy

# Deploy with specific Dockerfile
fly deploy --dockerfile Dockerfile.production

# Deploy without cache
fly deploy --no-cache
```

### Deployment Strategies

**Rolling (default)**:
```toml
[deploy]
  strategy = "rolling"
```

**Blue-Green**:
```toml
[deploy]
  strategy = "bluegreen"
```

**Immediate**:
```toml
[deploy]
  strategy = "immediate"
```

## Scaling

### Vertical Scaling

```bash
# Increase machine size
fly scale vm shared-cpu-2x

# Add memory
fly scale memory 512
```

### Horizontal Scaling

```bash
# Set machine count
fly scale count 3

# Scale by region
fly scale count 2 --region iad
fly scale count 2 --region cdg
```

### Auto-scaling

```toml
[http_service]
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 1

  [http_service.concurrency]
    type = "requests"
    soft_limit = 200
    hard_limit = 250
```

## Regions

### Available Regions

Popular regions:
- `iad` - Ashburn, Virginia (US East)
- `lax` - Los Angeles (US West)
- `cdg` - Paris (Europe)
- `nrt` - Tokyo (Asia)
- `syd` - Sydney (Australia)

### Multi-Region Deployment

```bash
# Add regions
fly regions add cdg nrt

# Set primary region
fly regions set iad

# View regions
fly regions list
```

## Persistent Storage

### Volumes

```bash
# Create volume
fly volumes create myapp_data --size 10 --region iad

# List volumes
fly volumes list
```

Mount in `fly.toml`:

```toml
[mounts]
  source = "myapp_data"
  destination = "/data"
```

### Managed Postgres

```bash
# Create Postgres cluster
fly postgres create --name my-db

# Attach to app
fly postgres attach my-db

# Connect locally
fly proxy 5432 -a my-db
```

### Managed Redis

```bash
# Create Redis
fly redis create --name my-redis

# Get connection string
fly redis status my-redis
```

## Health Checks

### HTTP Health Check

```toml
[http_service]
  internal_port = 8080

  [[http_service.checks]]
    interval = "10s"
    timeout = "2s"
    grace_period = "5s"
    method = "GET"
    path = "/health"
```

### TCP Health Check

```toml
[[services.tcp_checks]]
  interval = "10s"
  timeout = "2s"
  grace_period = "5s"
```

## Monitoring

### Logs

```bash
# Stream logs
fly logs

# View recent logs
fly logs --no-tail
```

### Status

```bash
# App status
fly status

# Machine status
fly machine list
```

### Metrics

```bash
# Open Grafana dashboard
fly dashboard
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Fly.io

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: superfly/flyctl-actions/setup-flyctl@master

      - run: flyctl deploy --remote-only
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

### Getting Deploy Token

```bash
fly tokens create deploy -x 999999h
```

Add as `FLY_API_TOKEN` in GitHub repository secrets.

## SSH Access

```bash
# SSH into running machine
fly ssh console

# Run command
fly ssh console -C "ls -la /app"
```

## Local Development

### Connect to Fly Postgres Locally

```bash
# Start proxy
fly proxy 5432 -a my-db

# Connect with psql
psql postgres://postgres:password@localhost:5432/my_db
```

### Wireguard VPN

```bash
# Create WireGuard config
fly wireguard create

# Import to WireGuard client
# Then access internal services directly
```

## Troubleshooting

### Deployment Failures

```bash
# View deployment logs
fly logs --instance <instance-id>

# Check machine status
fly machine list
fly machine status <machine-id>
```

### Out of Memory

Increase memory in `fly.toml`:
```toml
[[vm]]
  memory_mb = 512  # or 1024, 2048
```

### Health Check Failures

```bash
# Check health endpoint locally
curl http://localhost:8080/health

# View health check logs
fly logs | grep health
```

### Connection Issues

```bash
# Test connectivity
fly ping

# Check DNS
fly dig my-app.fly.dev
```

## Related

- [Environment Syncing](../environments/env-syncing.md)
- [Secret Management](../security/secret-management.md)
- [HUMAN Follow-up](../tickets/human-followup-deployment.md)
