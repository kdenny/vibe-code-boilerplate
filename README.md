# Vibe Code Boilerplate

A framework-agnostic, AI-agent-agnostic project boilerplate that orchestrates ticket workflows, GitHub/PR/CI enforcement, git worktrees, and secure environment handling.

**What this is:** A workflow orchestration layer for AI-assisted development — ticket tracking, Git automation, CI/CD enforcement.

**What this is NOT:** An application boilerplate with pre-built app structure (React, FastAPI, etc.). You build your app structure on top of this.

## What This Is

This boilerplate provides:
- **Ticket Integration** - Connect to Linear (Shortcut coming soon)
- **Git Workflow Automation** - Worktrees, branch naming, rebasing
- **PR Policy Enforcement** - Risk labels, ticket references, testing instructions
- **Secret Management** - Allowlists, provider sync, scanning
- **CI/CD Templates** - Security scanning, test detection, SBOM generation
- **Recipe Library** - Best practices documentation for common tasks

## When to Use It

Use this boilerplate when:
- Starting a new project with AI-assisted development
- You want consistent workflows across projects
- You need ticket tracking integration
- You want enforced PR standards

### Example Prompt for AI Agents

```
I'm starting a new project. Reference the vibe-code-boilerplate at
[path/to/boilerplate] for:
- Project structure conventions
- Git workflow (worktrees, rebasing)
- PR templates and policies
- Ticket tracking integration

Follow the recipes in recipes/ for specific implementations.
```

## Quick Start

### 1. Run Setup Wizard

```bash
bin/vibe setup
```

This will prompt you for:
- GitHub authentication (gh CLI or PAT)
- Ticket tracker (Linear)
- Optional: Branch naming, environment configuration

### 2. Verify Setup

```bash
bin/doctor
```

### 3. Start Working

```bash
# Start working on a ticket or GitHub issue (creates worktree from latest main)
bin/vibe do PROJ-123   # or: bin/vibe do 21  for GitHub issue #21

# You'll be in a new worktree with the branch ready
cd ../your-project-worktrees/PROJ-123

# When done, open a PR (run from inside the worktree)
bin/vibe pr
```

`bin/vibe do` fetches latest `main` and creates the new branch from `origin/main`, so you always start from a fresh base. You can run it from the main repo or from any worktree.

## Branch Naming

Branches follow the pattern in `.vibe/config.json`:

```
{PROJ}-{num}  →  PROJ-123
```

**ELI5**: Your branch name should start with your ticket ID. If your ticket is `PROJ-123`, your branch is `PROJ-123` or `PROJ-123-add-feature`.

This lets the system:
- Link PRs to tickets automatically
- Track work in progress
- Enforce PR policies

## Script Reference

| Script | Description |
|--------|-------------|
| `bin/vibe setup` | Initial configuration wizard |
| `bin/vibe do <ticket>` | Start work on a ticket (creates worktree) |
| `bin/vibe doctor` | Check project health |
| `bin/doctor` | Shortcut for `bin/vibe doctor` |
| `bin/ticket list` | List tickets from tracker |
| `bin/ticket get <id>` | Get ticket details |
| `bin/secrets list` | List configured secrets |
| `bin/secrets sync` | Sync secrets to providers |

## Workflow Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         DEVELOPMENT FLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  1. TICKET          2. WORKTREE         3. CODE                  │
│  ┌─────────┐       ┌───────────┐       ┌─────────┐              │
│  │ PROJ-123│  ───► │ bin/vibe  │  ───► │ Write   │              │
│  │ in Linear│       │ do PROJ-123│      │ Code    │              │
│  └─────────┘       └───────────┘       └─────────┘              │
│                           │                  │                   │
│                           ▼                  ▼                   │
│                    ../project-worktrees/    git commit           │
│                    └── PROJ-123/                                 │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  4. REBASE          5. PR               6. REVIEW                │
│  ┌─────────┐       ┌───────────┐       ┌─────────┐              │
│  │ git     │  ───► │ gh pr     │  ───► │ CI runs │              │
│  │ rebase  │       │ create    │       │ Review  │              │
│  └─────────┘       └───────────┘       └─────────┘              │
│       │                  │                  │                    │
│       ▼                  ▼                  ▼                    │
│  Always rebase,     Risk label,        PR policy                │
│  never merge        ticket ref         enforced                  │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  7. MERGE           8. CLEANUP                                   │
│  ┌─────────┐       ┌───────────┐                                │
│  │ Squash  │  ───► │ git       │                                │
│  │ & merge │       │ worktree  │                                │
│  └─────────┘       │ remove    │                                │
│                    └───────────┘                                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
.
├── .vibe/                    # Configuration
│   ├── config.json           # Main config (committed)
│   ├── local_state.json      # Runtime state (gitignored)
│   ├── secrets.allowlist.json # Allowed secrets
│   └── grandfathered_tickets.md
├── bin/                      # CLI scripts
│   ├── vibe                  # Main entry point
│   ├── doctor                # Health check
│   ├── ticket                # Ticket operations
│   └── secrets               # Secret management
├── lib/vibe/                 # Python library
│   ├── config.py             # Config management
│   ├── state.py              # State management
│   ├── doctor.py             # Health checks
│   ├── trackers/             # Ticket integrations
│   ├── git/                  # Git operations
│   ├── secrets/              # Secret management
│   ├── wizards/              # Setup wizards
│   └── cli/                  # CLI commands
├── recipes/                  # Best practices docs
│   ├── architecture/         # ADRs, decision docs
│   ├── agents/               # AI agent guidelines
│   ├── environments/         # Env management
│   ├── security/             # Security practices
│   ├── workflows/            # Git, PR workflows
│   ├── tickets/              # Tracker setup
│   ├── frameworks/           # React, Next.js, etc.
│   ├── testing/              # Test frameworks
│   ├── deployment/           # Vercel, Fly.io
│   ├── databases/            # Supabase, Postgres
│   └── observability/        # Sentry, debugging
├── technical_docs/           # Project documentation
│   └── adr-template.md       # ADR template
├── .github/
│   ├── workflows/            # CI/CD
│   │   ├── security.yml      # Secret scanning, SBOM
│   │   ├── pr-policy.yml     # PR validation
│   │   └── tests.yml         # Test runner
│   └── PULL_REQUEST_TEMPLATE.md
├── CLAUDE.md                 # AI agent instructions (must be all caps so tools load it)
├── README.md                 # This file
├── pyproject.toml            # Python deps
├── .gitignore
└── .env.example              # Environment template
```

## Recipes

Recipes are markdown guides for common tasks. Each has:
- **When to use** - Scenarios where the recipe applies
- **Step-by-step instructions** - How to implement
- **Extension points** - How to customize

### Key Recipes

| Recipe | Description |
|--------|-------------|
| `workflows/git-worktrees.md` | Using worktrees for parallel work |
| `workflows/branching-and-rebasing.md` | Rebase workflow |
| `workflows/pr-risk-assessment.md` | Risk labeling guide |
| `security/secret-management.md` | Secrets philosophy |
| `agents/asking-clarifying-questions.md` | AI agent guidelines |
| `tickets/linear-setup.md` | Linear integration |

## Configuration

Main configuration is in `.vibe/config.json`:

```json
{
  "tracker": {
    "type": "linear",
    "config": { "team_id": "..." }
  },
  "github": {
    "auth_method": "gh_cli",
    "owner": "your-org",
    "repo": "your-repo"
  },
  "branching": {
    "pattern": "{PROJ}-{num}",
    "main_branch": "main",
    "always_rebase": true
  },
  "labels": {
    "type": ["Bug", "Feature", "Chore", "Refactor"],
    "risk": ["Low Risk", "Medium Risk", "High Risk"],
    "area": ["Frontend", "Backend", "Infra", "Docs"],
    "special": ["HUMAN", "Milestone", "Blocked"]
  }
}
```

## Known Limitations

### Shortcut Integration (GitHub Issue #1)
Shortcut.com tracker integration is stubbed but not implemented. Currently, only Linear is fully supported.

### Grandfathered Tickets (GitHub Issue #2)
Automated handling of pre-existing tickets that don't follow conventions is not yet implemented. Use manual grandfathering process documented in `recipes/tickets/ticket-audit-and-grandfathering.md`.

## Requirements

- Python 3.11+
- Git
- GitHub CLI (`gh`) - recommended
- Linear account - for ticket tracking

## Contributing

See `CLAUDE.md` for AI agent contribution guidelines. For human contributors:

1. Fork and create a feature branch
2. Follow the PR template
3. Ensure `bin/doctor` passes
4. Add tests if applicable

## License

MIT
