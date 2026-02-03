# Vibe Code Boilerplate

**Ship faster with AI. Stay organized. Never lose work.**

A workflow orchestration layer for AI-assisted development that actually works. Linear integration, automatic ticket status updates, git worktrees for parallel work, PR policies that enforce quality.

```
Linear ticket → bin/vibe do PROJ-123 → Worktree created → Code → PR → Merge → Ticket auto-updated to Deployed
```

**What this is:** Production-ready workflows for AI-assisted development — ticket tracking, Git automation, CI/CD enforcement.

**What this is NOT:** An application boilerplate (React, FastAPI, etc.). You build your app structure on top of this foundation.

## What This Is

This boilerplate provides:
- **Linear Integration** - Full CRUD, automatic status updates, label management
- **Automatic Ticket Updates** - PR opened → In Review, PR merged → Deployed (zero manual status changes)
- **Local Hooks** - Ticket auto-marked "In Progress" when you mention it (optional)
- **Git Worktrees** - Each ticket gets isolated workspace, no branch switching conflicts
- **PR Policy Enforcement** - Risk labels, ticket references, testing instructions
- **Multi-Agent Coordination** - Guidelines for multiple AI agents working simultaneously
- **Secret Management** - Allowlists, provider sync, Gitleaks scanning
- **Recipe Library** - 30+ best practices guides for common tasks
- **HUMAN follow-up tickets** - Auto-create HUMAN-labeled tickets for deployment setup

## When to Use It

Use this boilerplate when:
- Starting a new project with AI-assisted development
- **Retrofitting an existing project** with standardized workflows
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

### 2. Update CLAUDE.md

**Important:** Open `CLAUDE.md` and fill in the **Project Overview** section:
- What this project does
- Tech stack (backend, frontend, database, deployment)
- Key features / domains

AI agents use this context to help you effectively.

### 3. Add Linear API Key (if using Linear)

```bash
# Add to .env.local (gitignored)
echo "LINEAR_API_KEY=lin_api_your_key_here" >> .env.local
```

Get your key from [Linear Settings → API](https://linear.app/settings/api).

### 4. Verify Setup

```bash
bin/vibe doctor
```

### 5. Start Working

```bash
# Start working on a ticket or GitHub issue (creates worktree from latest main)
bin/vibe do PROJ-123   # or: bin/vibe do 21  for GitHub issue #21

# You'll be in a new worktree with the branch ready
cd ../your-project-worktrees/PROJ-123

# When done, open a PR (run from inside the worktree)
bin/vibe pr
```

`bin/vibe do` fetches latest `main` and creates the new branch from `origin/main`, so you always start from a fresh base. You can run it from the main repo or from any worktree.

## Retrofitting Existing Projects

Already have a project? Use `retrofit` to add boilerplate workflows without starting over:

```bash
# Run from your existing project directory
bin/vibe retrofit --analyze-only  # See what would change
bin/vibe retrofit                  # Interactive guided adoption
```

Retrofit automatically detects:
- **Git configuration**: main/master branch, existing branch patterns
- **Frameworks**: React, Next.js, Vue, FastAPI, Django, etc.
- **Deployment**: Vercel, Fly.io, Docker configs
- **Database**: Supabase, Neon, Postgres, etc.
- **Existing workflows**: Preserves your GitHub Actions

Then it applies only what's missing:
- `.vibe/config.json` with detected settings
- PR template with risk assessment
- GitHub labels (type, risk, area)
- Minimal CI workflows (security, PR policy)

See `recipes/workflows/retrofit-guide.md` for the full guide.

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
| `bin/vibe retrofit` | Apply boilerplate to existing project |
| `bin/vibe do <ticket>` | Start work on a ticket (creates worktree) |
| `bin/vibe doctor` | Check project health |
| `bin/doctor` | Shortcut for `bin/vibe doctor` |
| `bin/ticket list` | List tickets from tracker |
| `bin/ticket get <id>` | Get ticket details |
| `bin/ticket create <title>` | Create a new ticket |
| `bin/ticket update <id>` | Update ticket status/title/labels |
| `bin/ticket labels` | List all labels with their IDs |
| `bin/ticket create-human-followup` | Create HUMAN follow-up ticket for deployment |
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
├── .claude/                  # Claude Code integration
│   ├── hooks/                # Local automation scripts
│   │   ├── linear-start-ticket.sh   # Auto "In Progress"
│   │   └── linear-update-on-commit.sh  # Auto "Done"
│   └── settings.local.json.example
├── .github/
│   ├── workflows/            # CI/CD
│   │   ├── security.yml      # Secret scanning, SBOM
│   │   ├── pr-policy.yml     # PR validation
│   │   ├── pr-opened.yml     # Linear → In Review
│   │   ├── pr-merged.yml     # Linear → Deployed
│   │   ├── lint.yml          # Python linting
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
| `workflows/retrofit-guide.md` | Apply boilerplate to existing projects |
| `workflows/linear-hooks.md` | Local hooks for automatic Linear updates |
| `workflows/pr-opened-linear.md` | PR opened → In Review automation |
| `workflows/pr-merge-linear.md` | PR merged → Deployed automation |
| `workflows/multi-agent-coordination.md` | Multiple AI agents working together |
| `workflows/git-worktrees.md` | Using worktrees for parallel work |
| `security/secret-management.md` | Secrets philosophy |
| `agents/human-required-work.md` | When to create HUMAN tickets |
| `tickets/linear-setup.md` | Linear integration |
| `tickets/linear-label-ids.md` | Using label IDs in API calls |

## Configuration

Main configuration is in `.vibe/config.json`:

```json
{
  "tracker": {
    "type": "linear",
    "config": { "team_id": "...", "deployed_state": "Deployed" }
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

### Automatic Linear Status Updates

**Recommended: Use Linear's native GitHub integration** for automatic status updates. It's simpler to set up and maintained by Linear.

1. In Linear: **Settings → Integrations → GitHub → Connect**
2. Authorize and select your repositories
3. Configure workflow automation (PR opened → In Review, PR merged → Done)

See `recipes/tickets/linear-github-integration.md` for detailed setup.

**Fallback: Custom GitHub Actions** (for GitHub Enterprise or custom requirements)

| Event | Workflow | Status Change |
|-------|----------|---------------|
| PR opened | `pr-opened.yml` | → In Review |
| PR merged | `pr-merged.yml` | → Deployed |

Fallback setup:
1. Add repository secret `LINEAR_API_KEY` (from [Linear Settings → API](https://linear.app/settings/api))
2. Optional: Set repository variable `LINEAR_DEPLOYED_STATE` (default: `Deployed`)
3. Optional: Set repository variable `LINEAR_IN_REVIEW_STATE` (default: `In Review`)

### Local Hooks (Optional)

For even faster feedback, enable local Claude Code hooks:

```bash
cp .claude/settings.local.json.example .claude/settings.local.json
```

| Trigger | Action |
|---------|--------|
| Mention ticket in prompt | Marks ticket "In Progress" |
| Git commit with ticket ID | Marks ticket "Done" |

See `recipes/workflows/linear-hooks.md` for details.

## Supported Trackers

- **Linear** - Full integration with native GitHub support (recommended)
- **Shortcut** - Full integration via API (see `recipes/tickets/shortcut.md`)

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
