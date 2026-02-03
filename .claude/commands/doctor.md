---
description: Run comprehensive health checks on the project
allowed-tools: Bash
---

# /doctor - Check project health

Run comprehensive health checks on the project configuration, integrations, and GitHub Actions.

## Usage

```
/doctor
/doctor --verbose
/doctor --github-actions    # Also check GitHub secrets and workflow runs
```

## What it checks

### Core Checks
- Valid `.vibe/config.json`
- Python version (3.11+)
- Git installation and repository
- GitHub CLI (`gh`) authentication
- Gitignore entries

### Integrations
- **Tracker**: Linear or Shortcut configuration + API key
- **PromptVault**: API key for LLM apps
- **Fly.io**: CLI authentication
- **Vercel**: CLI authentication
- **Supabase**: CLI or environment variables
- **Local hooks**: Claude Code hooks configuration

### GitHub Actions (with `--github-actions`)
- Required secrets (LINEAR_API_KEY, etc.)
- Recent workflow run status

## Instructions

When the user invokes `/doctor`:

1. Run `bin/vibe doctor` (or with flags)
2. Report results grouped by category:
   - Core Checks
   - Integrations
   - GitHub Actions (if requested)
3. For warnings/failures, show fix hints
4. Summarize: X/Y passed, N warnings, M skipped

## Example Output

```
==================================================
  Vibe Doctor - Health Check
==================================================

  Core Checks
  ------------------------------
  ✓ Config file: .vibe/config.json exists
  ✓ Gitignore: All required entries present
  ✓ Python version: Python 3.11
  ✓ Git: Git repository detected
  ✓ GitHub CLI: gh CLI authenticated

  Integrations
  ------------------------------
  ✓ Tracker: Linear configured with API key
  ○ PromptVault: Not configured (optional)
      → Add PROMPTVAULT_API_KEY to .env.local for LLM apps
  ✓ Fly.io: CLI authenticated
  ○ Vercel: CLI not installed (optional)
  ○ Supabase: Not configured (optional)
  ○ Local hooks: Not configured (optional)

  GitHub Actions
  ------------------------------
  ✓ GH Secret: LINEAR_API_KEY: Secret exists
  ✓ Recent workflows: All recent runs passed

  12/14 passed, 0 warnings, 2 skipped
```

## Status Icons

| Icon | Status | Meaning |
|------|--------|---------|
| ✓ | PASS | Check passed |
| ⚠ | WARN | Warning - should address |
| ✗ | FAIL | Failed - must fix |
| ○ | SKIP | Skipped (optional/not configured) |

## Common Issues

| Issue | Fix |
|-------|-----|
| Python < 3.11 | Install Python 3.11+ via pyenv or brew |
| gh not authenticated | Run `gh auth login` |
| No tracker configured | Run `bin/vibe setup --wizard tracker` |
| LINEAR_API_KEY not set | Add to .env.local |
| Fly.io not authenticated | Run `fly auth login` |
| Vercel not authenticated | Run `vercel login` |

## Interactive Setup

If many integrations are skipped/warned, suggest:

```
Would you like to run the integration setup wizard?
Run: bin/vibe setup --wizard integrations
```
