# Integration Freshness Tracking

This recipe explains how to track and verify integration documentation stays current.

## Overview

Third-party integrations (Vercel, Fly.io, Supabase, etc.) change over time:
- CLI commands evolve
- Authentication flows update
- Configuration formats change
- Environment variables get renamed

Stale documentation leads to failed setups and wasted time. This system tracks when each integration was last verified and alerts when re-verification is needed.

## Components

### 1. Freshness Data (`.vibe/integration-freshness.json`)

Tracks when each integration was last verified:

```json
{
  "$schema": "./integration-freshness.schema.json",
  "integrations": {
    "vercel": {
      "last_checked": "2026-02-02",
      "checked_by": "agent",
      "version_checked": "vercel@37.x",
      "notes": "CLI install, auth, project linking, env pull"
    }
  }
}
```

Fields:
- `last_checked`: Date of last verification (YYYY-MM-DD)
- `checked_by`: Who verified (agent, human name, or CI)
- `version_checked`: CLI/API version that was tested
- `notes`: What was specifically verified

### 2. Doctor Check

`bin/vibe doctor` includes an integration freshness check that warns if any integration hasn't been verified in over 30 days.

### 3. GitHub Action (`.github/workflows/integration-freshness.yml`)

Runs monthly (1st of each month) to:
1. Check for stale integrations (> 30 days)
2. Create a GitHub issue if any are found
3. Add comments to existing issues if already open

## Verification Checklist

When re-verifying an integration, check:

- [ ] CLI installation command still works
- [ ] Authentication flow unchanged
- [ ] Configuration file format unchanged
- [ ] Environment variable names unchanged
- [ ] Recipe documentation matches current CLI output
- [ ] Wizard steps match current workflow

## Updating After Verification

After verifying an integration works correctly:

```bash
# Edit .vibe/integration-freshness.json
{
  "integrations": {
    "fly": {
      "last_checked": "2026-02-15",  # Update to today
      "checked_by": "your-name",
      "version_checked": "flyctl@0.3.50",  # Current version
      "notes": "Verified deploy, secrets, postgres"
    }
  }
}
```

Then commit the change:

```bash
git add .vibe/integration-freshness.json
git commit -m "chore: update fly integration freshness"
```

## Adding New Integrations

When adding a new integration to the boilerplate:

1. Add entry to `.vibe/integration-freshness.json`
2. Create recipe in `recipes/integrations/`
3. Add wizard if applicable
4. Document in CLAUDE.md recipes reference

## Tracked Integrations

Current integrations tracked:

| Integration | Type | Recipe |
|------------|------|--------|
| Vercel | Hosting | `recipes/integrations/vercel.md` |
| Fly.io | Hosting | `recipes/integrations/fly.md` |
| Supabase | Database | `recipes/integrations/supabase.md` |
| Neon | Database | `recipes/integrations/neon.md` |
| Sentry | Monitoring | `recipes/integrations/sentry.md` |
| Linear | Tracker | `recipes/tickets/linear-setup.md` |

## Handling Stale Integrations

When the monthly check finds stale integrations:

1. A GitHub issue is created with the `Chore` and `HUMAN` labels
2. Review the verification checklist for each stale integration
3. Update the freshness file with new dates
4. Close the issue

If an integration has significantly changed:
1. Update the corresponding recipe
2. Update any related wizards
3. Test the full setup flow
4. Update freshness file
