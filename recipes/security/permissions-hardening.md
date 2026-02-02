# GitHub Actions Permissions Hardening

## When to Use This Recipe

Use this recipe when you need to:
- Set up new GitHub Actions workflows
- Audit existing workflow permissions
- Understand the principle of least privilege for CI/CD
- Prevent supply chain attacks via Actions

## Default Permissions Problem

By default, GitHub Actions get broad permissions. This is risky because:
- Compromised dependencies can steal secrets
- Malicious PRs can exfiltrate data
- Over-permissioned tokens increase blast radius

## Minimal Permissions Pattern

Always declare explicit permissions at the workflow level:

```yaml
name: CI

on: [push, pull_request]

# Restrict all jobs to read-only by default
permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      # ...
```

## Common Permission Sets

### Read-only CI (linting, testing)
```yaml
permissions:
  contents: read
```

### PR Comments/Status Checks
```yaml
permissions:
  contents: read
  pull-requests: write
```

### Create Releases
```yaml
permissions:
  contents: write
```

### Security Scanning
```yaml
permissions:
  contents: read
  security-events: write
```

### Deploy to GitHub Pages
```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

## Job-Level Permissions

For more granular control, set permissions per job:

```yaml
permissions:
  contents: read  # Workflow default

jobs:
  test:
    runs-on: ubuntu-latest
    # Inherits workflow permissions
    steps: [...]

  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Only this job can write
    steps: [...]
```

## Third-Party Action Security

### Pin to SHA, Not Tags
```yaml
# Bad - tag can be moved to malicious commit
- uses: some/action@v1

# Good - immutable reference
- uses: some/action@a1b2c3d4e5f6...
```

### Audit Before Using
1. Check the action's source code
2. Look at recent commits
3. Verify maintainer reputation
4. Prefer official actions (actions/*)

### Use Dependabot for Updates
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

## Secrets in Actions

### Access Patterns
```yaml
# Repository secret
${{ secrets.API_KEY }}

# Environment secret (requires approval)
environment: production
secrets: inherit  # Or explicit list
```

### Never Echo Secrets
```yaml
# Bad - might leak in logs
- run: echo ${{ secrets.API_KEY }}

# Good - mask automatically
- run: some-command
  env:
    API_KEY: ${{ secrets.API_KEY }}
```

## Audit Checklist

- [ ] All workflows declare explicit `permissions:`
- [ ] No workflow has `permissions: write-all`
- [ ] Third-party actions pinned to SHA
- [ ] Secrets not echoed or logged
- [ ] PR workflows from forks have limited permissions
- [ ] Dependabot configured for action updates

## Extension Points

- Add custom action verification steps
- Implement workflow approval gates
- Set up OIDC for cloud deployments
