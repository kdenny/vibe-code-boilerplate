# Vibe Code Boilerplate

**Ship faster with AI. Stay organized. Never lose work.**

A workflow orchestration layer for AI-assisted development that actually works. Linear integration, automatic ticket status updates, git worktrees for parallel work, PR policies that enforce quality.

```
Linear ticket → bin/vibe do PROJ-123 → Worktree created → Code → PR → Merge → Ticket auto-updated to Deployed
```

**What this is:** Production-ready workflows for AI-assisted development — ticket tracking, Git automation, CI/CD enforcement.

**What this is NOT:** An application boilerplate (React, FastAPI, etc.). You build your app structure on top of this foundation.

## Why Use This?

**The short answer:** Close the loop between your tickets and your code automatically.

### What you can do with this that you can't do with vanilla Claude Code

| Capability | Vanilla Claude Code | With This Boilerplate |
|------------|--------------------|-----------------------|
| Ticket → branch → code → PR | Manual setup each time | `bin/vibe do PROJ-123` - one command |
| Ticket auto-updates on PR open/merge | None | Automatic (In Progress → In Review → Deployed) |
| Worktree per ticket | Manual `git worktree` commands | Automatic, with cleanup |
| PR risk labels enforced | Hope you remember | CI blocks PR without label |
| Ticket reference in PR required | Hope you remember | CI blocks PR without ref |
| Multi-agent conflict prevention | Roll your own | Built-in guidelines + worktree isolation |

### The 80/20 - Features that deliver most value

1. **Ticket lifecycle automation** - Open ticket, do `bin/vibe do`, code, PR, merge. Ticket status updates itself. Zero manual status changes.
2. **Worktree isolation** - Each ticket gets its own directory. No branch switching. No stashing. Work on multiple tickets in parallel.
3. **PR policy enforcement** - CI ensures every PR has a ticket reference and risk label. No more "oops I forgot" PRs.

### Minimal setup to get value

```bash
bin/vibe setup --quick   # ~1 minute, sensible defaults
```

That's it. You get:
- PR template with risk assessment
- Branch naming convention
- Worktree management via `bin/vibe do`

Add Linear integration later when you're ready: `bin/vibe setup -w tracker`

## Feature Classification

This boilerplate provides three types of features relative to vanilla Claude Code:

| Type | Description | Examples |
|------|-------------|----------|
| **Core** | Unlikely to be replaced by Claude Code | Linear/Shortcut integration, ticket→PR lifecycle automation, PR policy enforcement |
| **Complementary** | Enhances Claude Code's native features | Worktree management, multi-agent coordination, risk assessment workflows |
| **Recipes** | Reference documentation that may overlap with Claude Code docs | Best practices, framework guides, debugging tips |

## Tracker Dependency

**This boilerplate is Linear-first.** The ticket automation features are built around Linear's API.

- **Linear**: Full support (recommended)
- **Shortcut**: Supported via API
- **GitHub Issues/Jira/Notion**: Not currently supported

If you don't use Linear or Shortcut, you can still use:
- Worktree management (`bin/vibe do <branch-name>`)
- PR template and policy enforcement
- Multi-agent coordination guidelines
- Recipe library

## What This Provides

- **Linear Integration** - Full CRUD, automatic status updates, label management
- **Automatic Ticket Updates** - PR opened → In Review, PR merged → Deployed (zero manual status changes)
- **Local Hooks** - Ticket auto-marked "In Progress" when you mention it (optional)
- **Git Worktrees** - Each ticket gets isolated workspace, no branch switching conflicts
- **PR Policy Enforcement** - Risk labels, ticket references, testing instructions
- **Multi-Agent Coordination** - Guidelines for multiple AI agents working simultaneously
- **Secret Management** - Allowlists, provider sync, Gitleaks scanning
- **Recipe Library** - 30+ best practices guides for common tasks
- **HUMAN follow-up tickets** - Auto-create HUMAN-labeled tickets for deployment setup
- **Multi-Assistant Support** - Generate instruction files for Claude, Cursor, Copilot from single source
- **Figma Integration** - Design-to-code workflow with codebase context for Figma AI prompts

## Works With Any Language

**This boilerplate works with any tech stack** — JavaScript/TypeScript, Go, Rust, Ruby, Java, or any other language.

The CLI tools (`bin/vibe`, `bin/ticket`) are written in Python, but they run **alongside** your project, not as part of it:

| Component | Language | Part of your app? |
|-----------|----------|-------------------|
| `bin/vibe`, `bin/ticket` CLI | Python | No — workflow tooling only |
| GitHub Actions workflows | YAML | No — CI/CD automation |
| PR templates, CLAUDE.md | Markdown | No — documentation |
| Your application code | **Any language** | Yes |

**What this means:**
- No Python dependencies in your `package.json`, `Cargo.toml`, `go.mod`, etc.
- Your app's build/test/deploy remains unchanged
- Works with monorepos containing multiple languages
- The Python tooling only handles workflow automation (tickets, worktrees, PR policies)

**Example stacks that work out of the box:**
- Next.js + Vercel
- Go + Fly.io
- Rust + Docker
- Ruby on Rails
- Any combination in a monorepo

## How We Compare

This boilerplate focuses on **workflow automation** rather than context engineering or component marketplaces.

| Feature | This Boilerplate | Alternatives |
|---------|------------------|--------------|
| Ticket Integration | Linear, Shortcut with auto-status | Most have none |
| Worktree Management | Built-in | Rare |
| PR Policy Enforcement | Risk labels, ticket refs | Common but simpler |
| Multi-Assistant Support | Claude, Cursor, Copilot | botingw has 10+ |
| MCP Servers | Not built-in | serpro69, davila7 |
| Sub-Agent Architecture | Not built-in (planned) | shinpr has this |

**Best for**: Teams using Linear/Shortcut who want automated ticket→PR→deploy lifecycle.

**Also good for**: Teams who want PR policy enforcement and worktree management even without a ticket tracker.

**Not best for**: Teams wanting Jira/GitHub Issues integration, component marketplaces, or MCP servers.

See [docs/competitive-analysis.md](docs/competitive-analysis.md) for detailed comparison.

## New to Development?

If you're new to software development, here's what you need to know to use this boilerplate effectively.

### Key Terms Explained

| Term | What It Means | Why It Matters |
|------|---------------|----------------|
| **Repository (repo)** | A folder that Git tracks. Contains your code plus its entire history. | This boilerplate is a repo. Your project will be a repo. |
| **Branch** | A parallel version of your code. Like a "save slot" you can switch between. | Lets you work on features without breaking the main code. |
| **Worktree** | A separate copy of your repo in its own folder, pointing to a specific branch. | Work on multiple features simultaneously without switching branches. |
| **PR (Pull Request)** | A request to merge your branch's changes into the main branch. Others can review it first. | How your code gets from "done" to "deployed". |
| **Ticket** | A task in a project management tool (Linear, Shortcut). Has a title, description, and status. | Tracks what you're working on and why. |
| **CI (Continuous Integration)** | Automated checks that run when you submit a PR. Tests, linting, security scans. | Catches problems before they reach production. |

### The Development Flow (Step by Step)

Here's what happens when you work on a feature:

```
1. You have a ticket (PROJ-123: "Add login button")
   ↓
2. Run: bin/vibe do PROJ-123
   → Creates a separate folder for your work
   → You won't accidentally break other code
   ↓
3. Write your code (or have AI write it)
   → All changes stay in your folder
   ↓
4. Run: bin/vibe pr
   → Creates a Pull Request for review
   → CI checks run automatically
   ↓
5. After approval, merge the PR
   → Your ticket status updates automatically
   → PROJ-123 goes from "In Review" → "Deployed"
```

### What You Need Before Starting

1. **Python 3.11+** - [Download here](https://www.python.org/downloads/)
2. **Git** - [Download here](https://git-scm.com/downloads)
3. **GitHub CLI (`gh`)** - [Install instructions](https://cli.github.com/)
4. **A GitHub account** - [Sign up free](https://github.com/)
5. *Optional:* A Linear account for ticket tracking - [Sign up free](https://linear.app/)

### Your First Project (5 Minutes)

```bash
# 1. Get this boilerplate
git clone https://github.com/kdenny/vibe-code-boilerplate.git my-project
cd my-project

# 2. Quick setup (no prompts, sensible defaults)
bin/vibe setup --quick

# 3. Verify everything works
bin/vibe doctor

# 4. Start building!
# Tell Claude/Cursor what you want to build.
```

### Getting Help

- **Stuck on a command?** Run it with `--help` (e.g., `bin/vibe setup --help`)
- **Something broken?** Run `bin/vibe doctor` to check your setup
- **Need examples?** Check the `recipes/` folder for step-by-step guides

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

## Quick Start (5 minutes)

Get productive immediately with minimal setup:

```bash
# 1. Quick setup (no prompts, sensible defaults)
bin/vibe setup --quick

# 2. Verify it worked
bin/vibe doctor

# 3. Start coding!
```

That's it. You now have:
- Git workflow defaults (branching, rebasing, worktrees)
- PR template with risk assessment
- Basic CLAUDE.md for AI agents

**Add integrations later** with `bin/vibe setup -w tracker` (Linear) or other wizards.

---

## Full Setup

For complete configuration including ticket tracking:

### Option A: Quick Setup (< 1 minute)

```bash
bin/vibe setup --quick
```

This sets up sensible defaults with no prompts:
- Git workflow (branching, worktrees, rebasing)
- PR template with risk assessment
- GitHub auto-configured from `gh` CLI

Add integrations later with `bin/vibe setup -w tracker`, `-w vercel`, etc.

### Option B: Full Setup (Interactive)

```bash
bin/vibe setup
```

This prompts you for:
- GitHub authentication (gh CLI or PAT)
- Ticket tracker (Linear/Shortcut)
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

**Note:** The CLI automatically loads `.env` files, so you don't need to `source` them manually. Load order:
1. `.env` - Base defaults
2. `.env.local` - Local overrides (gitignored)
3. `.env.{environment}` - Environment-specific (if `VIBE_ENV` or `NODE_ENV` is set)

To disable auto-loading: `VIBE_NO_DOTENV=1 bin/vibe ...`

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
| `design/figma-ai-prompts.md` | Optimizing Figma AI prompts with codebase context |
| `design/figma-to-code.md` | Design-to-implementation workflow |

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
