# Retrofit Guide: Applying Boilerplate to Existing Projects

This guide explains how to apply the vibe-code-boilerplate to an existing project that wasn't built with it from the start.

## When to Use Retrofit

Use `bin/vibe retrofit` when:
- You have an existing project without standardized workflows
- You want to adopt Linear/Shortcut ticket tracking
- You want to add PR policies and risk labels
- You want to enable git worktrees for parallel development
- You're joining a project that should use consistent tooling

## Quick Start

```bash
# Run from your existing project directory
bin/vibe retrofit --analyze-only  # First, see what would change
bin/vibe retrofit                  # Interactive mode (recommended)
bin/vibe retrofit --auto           # Apply all auto changes without prompting
```

## What Retrofit Detects

The analyzer automatically detects:

### Git Configuration
- **Main branch**: `main` vs `master` (from `origin/HEAD` or remote branches)
- **Branch patterns**: Analyzes existing feature branches to suggest naming conventions
- **Worktrees**: Whether worktrees are already in use

### Frameworks & Tools
- **Frontend**: React, Next.js, Vue, Nuxt, Svelte, Angular, Astro
- **Backend**: FastAPI, Django, Flask, Express, Hono
- **CSS**: Tailwind, Chakra UI, MUI, Bootstrap
- **Testing**: pytest, Vitest, Jest, Playwright, Cypress
- **Package manager**: Poetry, pipenv, pip, uv

### Deployment & Database
- **Hosting**: Vercel, Fly.io, Docker
- **Database**: Supabase, Neon, PostgreSQL, MySQL, MongoDB, Redis

### Existing Configuration
- **GitHub Actions**: Existing workflows (preserved, not overwritten)
- **PR templates**: Existing templates
- **Ticket tracking**: Linear or Shortcut environment variables

## Action Types

Retrofit categorizes actions into:

| Type | Meaning | Auto-Apply? |
|------|---------|-------------|
| **ADOPT** | New feature to add | Usually yes |
| **CONFIGURE** | Existing feature needs config | Usually yes |
| **SKIP** | Already configured | N/A |
| **CONFLICT** | Manual resolution needed | No |

## What Gets Applied

### Automatically Applied (with confirmation)

1. **`.vibe/config.json`** - Project configuration
   - Detected main branch
   - Detected or default branch pattern
   - Worktree settings

2. **`.vibe/local_state.json`** - Runtime state (gitignored)

3. **GitHub Actions** (if `--boilerplate-path` provided or minimal templates)
   - `pr-policy.yml` - Risk label enforcement
   - `security.yml` - Secret scanning

4. **PR Template** - `.github/PULL_REQUEST_TEMPLATE.md`

5. **GitHub Labels** - Type, risk, area, and special labels

### Requires Manual Configuration

- **Ticket tracking** - Run `bin/vibe setup -w tracker` after retrofit
- **Deployment** - Run `bin/vibe setup -w vercel` or `-w fly`
- **Database** - Run `bin/vibe setup -w database`

## Command Options

```bash
bin/vibe retrofit [OPTIONS]

Options:
  --analyze-only      Only show analysis, don't apply changes
  --dry-run           Show what would be done without making changes
  --auto              Apply all auto-applicable actions without prompting
  -b, --boilerplate-path PATH
                      Path to boilerplate source (for copying workflows)
```

## Examples

### Analyze First (Recommended)

```bash
# See what retrofit will detect and suggest
bin/vibe retrofit --analyze-only
```

Example output:
```
============================================================
  Retrofit Analysis Summary
============================================================

Detected Configuration:
------------------------------
  Main branch: main
  Branch pattern: {PROJ}-{num} (75% conf.)
  Frontend: next
  Backend: fastapi
  Package manager: poetry
  Database: Supabase
  Testing: pytest

Required Actions:
------------------------------
  [AUTO] Create .vibe/config.json with project settings
  [AUTO] Configure main branch as 'main'

Recommended Actions:
------------------------------
  [AUTO] Use detected branch pattern: '{PROJ}-{num}'
  [AUTO] Enable git worktrees for parallel development
  [AUTO] Add missing workflows: security, pr-policy
  [AUTO] Add PR template with risk assessment checklist
  [AUTO] Create standard GitHub labels (type, risk, area)

Already Configured (skipped):
------------------------------
  ✓ Supabase already configured
```

### Interactive Mode

```bash
bin/vibe retrofit
```

This will:
1. Show the analysis summary
2. List all auto-applicable actions
3. Ask for confirmation before applying
4. Show results for each action

### Non-Interactive Mode

```bash
bin/vibe retrofit --auto
```

Applies all auto-applicable actions without prompting. Good for CI/automation.

### With Boilerplate Source

```bash
bin/vibe retrofit --boilerplate-path ~/projects/vibe-code-boilerplate
```

Copies GitHub workflows from the boilerplate instead of using minimal templates.

## Handling Conflicts

When retrofit detects conflicting configuration:

```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
  CONFLICTS DETECTED - Manual resolution required
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

  • Unusual main branch detected: 'develop'
    Current: develop
    Suggested: main
    Consider using 'main' or 'master' for compatibility
```

**Resolution options:**
1. Keep your existing setup - update `.vibe/config.json` manually
2. Migrate to the standard - rename your branch and update CI
3. Use hybrid approach - keep branch but configure vibe to use it

## Post-Retrofit Steps

After running retrofit:

1. **Verify configuration**
   ```bash
   bin/vibe doctor
   ```

2. **Set up ticket tracking** (if desired)
   ```bash
   bin/vibe setup -w tracker
   ```

3. **Review generated files**
   - `.vibe/config.json` - Adjust settings as needed
   - `.github/workflows/` - Customize workflows if needed
   - `.github/PULL_REQUEST_TEMPLATE.md` - Customize template

4. **Update CLAUDE.md**
   - Fill in the Project Overview section
   - AI agents use this context to help effectively

5. **Commit the changes**
   ```bash
   git add .vibe .github
   git commit -m "chore: add vibe boilerplate configuration"
   ```

## Phased Adoption

For large teams, consider phased adoption:

### Phase 1: Configuration Only
```bash
bin/vibe retrofit --analyze-only  # Review
bin/vibe retrofit                 # Apply config only
```
Just adds `.vibe/config.json` and local state. No workflow changes.

### Phase 2: PR Policies
```bash
# Add PR template and labels
# Enable pr-policy.yml workflow
```
Team starts using risk labels and structured PRs.

### Phase 3: Ticket Integration
```bash
bin/vibe setup -w tracker
```
Connect to Linear/Shortcut for automatic status updates.

### Phase 4: Worktrees
Train team on worktree workflow:
```bash
bin/vibe do PROJ-123  # Creates isolated worktree
```

## Troubleshooting

### gh CLI not found
```
gh CLI not available. Install from https://cli.github.com/
```
**Solution:** Install GitHub CLI: `brew install gh` (macOS) or see https://cli.github.com/

### Label creation failed
```
Created 10 labels, failed 4: Bug, Feature, Chore, Refactor
```
**Solution:** Check GitHub permissions. You need write access to create labels.

### No auto-applicable actions
```
No auto-applicable actions found.
```
**Solution:** Project may already be configured. Run `bin/vibe doctor` to check status.

## See Also

- [Git Worktrees](./git-worktrees.md) - Using worktrees for parallel development
- [Branching and Rebasing](./branching-and-rebasing.md) - Git workflow
- [Linear Setup](../tickets/linear-setup.md) - Ticket tracker integration
- [PR Risk Assessment](./pr-risk-assessment.md) - Risk label guidelines
