# VIBE CODE BOILERPLATE — AUTHORITATIVE BUILD PROMPT

You are building a **framework-agnostic, AI-agent-agnostic project boilerplate** designed to orchestrate:
- Linear (primary) / Shortcut (secondary) ticket workflows
- GitHub + PR + CI enforcement
- Git worktrees with strict ticket ↔ branch ↔ PR coupling
- Secure env + secret handling
- Extensible recipes for frameworks, infra, testing, deployment, observability
- Human + agent collaboration without ambiguity

# ⚠️ THIS REPOSITORY IS **NOT MEANT TO BE FORKED** ⚠️

It is meant to be **referenced as source material** that agents replicate into new projects when instructed.

**Usage assumption:** The boilerplate is used in a **new empty app** or an app still in **early stages**. There should be no conflict between boilerplate structure and actual app code. If app code appears to conflict with the boilerplate and it cannot be resolved by a simple merge, **alert the user** to the issues and instruct them to fix before proceeding.

---

## CORE DESIGN PRINCIPLES (NON-NEGOTIABLE)

1. **Agent-first, human-readable**
   - Everything must be parseable by AI agents
   - Everything must be understandable by a non-technical human
2. **Interactive wizards for all necessary setup**
   - Every required setup step (tracker, branch naming, env/secrets, GitHub, etc.) must be drivable by an **interactive setup wizard** when config is missing or invalid.
   - If something is missing or ambiguous, run the relevant wizard; do not assume or guess. Block work that depends on that config until the wizard has been run (or config is supplied).
3. **Single source of truth**
   - `.vibe/config.json` is the canonical config
   - `CLAUDE.md` (all caps filename) mirrors this config in natural language rules
4. **No assumptions**
   - Never assume tools are installed
   - Detect → install → document
5. **Safety over convenience**
   - Secrets are never auto-synced without safeguards
   - Public vs secret env vars are strictly enforced
6. **Tickets drive everything**
   - No branch without a ticket
   - No PR without a ticket
   - No work without a fully specified ticket

---

## REQUIRED FILE STRUCTURE

```
/
├── README.md
├── CLAUDE.md
├── .vibe/
│   ├── config.json             # must include boilerplate.issues_url (canonical: https://github.com/kdenny/vibe-code-boilerplate/issues)
│   ├── local_state.json        # gitignored
│   ├── secrets.allowlist.json
│   └── grandfathered_tickets.md   # completed tickets from Linear/Shortcut that existed before boilerplate was added
├── bin/
│   ├── vibe
│   ├── doctor
│   ├── ticket
│   └── secrets
├── recipes/
│   ├── architecture/
│   ├── agents/
│   ├── environments/
│   ├── frameworks/
│   ├── testing/
│   ├── deployment/
│   ├── databases/
│   ├── observability/
│   ├── security/
│   └── workflows/
├── technical_docs/
│   └── adr-template.md
├── .github/
│   ├── workflows/
│   │   ├── security.yml
│   │   ├── pr-policy.yml
│   │   └── tests.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── .env.example
├── .gitignore
└── pyproject.toml (preferred; requirements.txt if minimal)
```

---

## RECIPES

Each recipe = one focused problem. **Markdown, copy-paste friendly.** No prose fluff; lots of commands + examples. Explicit **“When to use this recipe”** section at top. Document how recipes appear in the repo and in the README (links, copy-paste blocks at bottom).

### Recipe categories and expected content

**`/recipes/architecture/`**
- `adr-guide.md` — When ADRs are required; how to write them; how to reference them in tickets + PRs
- `alternatives-analysis.md` — Explicitly documenting rejected options

**`/recipes/security/`**
- `secret-management.md` — Public vs secret env vars; allowlist philosophy
- `permissions-hardening.md` — GitHub Actions permissions; least privilege examples
- `supply-chain.md` — Lockfiles; Dependabot vs Renovate tradeoffs

**`/recipes/environments/`**
- `env-syncing.md` — Local → CI → deploy; when automatic syncing is allowed
- `multi-env.md` — Local / Staging / Prod; how doctor validates each

**`/recipes/agents/`**
- `asking-clarifying-questions.md` — Examples of good vs bad clarifying questions
- `human-required-work.md` — When to apply the HUMAN label; how to pause safely without blocking progress
- `boilerplate-feedback.md` — When and how to file issues in the boilerplate repo (broken CLAUDE.md or recipes); `vibe boilerplate-issue` command

**`/recipes/workflows/`**
- `git-worktrees.md` — Why they exist; how `vibe do <ticket>` works; how cleanup happens
- `branching-and-rebasing.md` — Always rebase main; no merge commits
- `stacked-vs-milestone-prs.md` — When 1 PR per subtask is okay; when 1 PR per milestone is better
- `pr-risk-assessment.md` — How Low / Medium / High risk is determined; examples
- `testing-instructions-writing.md` — How to write instructions a non-technical reviewer can follow

**`/recipes/tickets/`**
- `linear-setup.md` — API key; required labels; workflow states (Backlog → In Progress → Deployed)
- `shortcut.md` — Epic mapping; differences from Linear
- `ticket-audit-and-grandfathering.md` — How legacy tickets are handled; machine-readable summary expectations

**`/recipes/frameworks/`**, **`/recipes/testing/`**, **`/recipes/deployment/`**, **`/recipes/databases/`**, **`/recipes/observability/`**
- **Testing:** Playwright, unit testing, getting them set up in GitHub Actions
- **Linting / hooks:** Linting and pre-commit hooks
- **Deployment:** Vercel, Fly.io, etc.
- **Databases:** Supabase, Neon, BYO Postgres
- **Observability:** Server logs (e.g. Sentry); debugging locally and on server

---

## SCRIPTING REQUIREMENTS

### Language + Runtime
- Core logic: **Python**
- Entry points: **Bash wrappers** — scripts in `bin/` are Bash entry points that invoke Python for core logic
- Single shared virtualenv for all scripts
- Scripts must:
  - auto-create + activate venv
  - install dependencies automatically
  - record installed tools + versions in `.vibe/local_state.json`

### Tools to Prefer
- **Prefer the assistant’s native integrations when available** (e.g. Cursor’s Linear UI); otherwise use API/CLI
- Use **gh CLI** if available, else GitHub API via PAT
- Use Linear API via Personal API Key when no native integration

---

## SETUP WIZARDS

Every necessary setup surface must have an interactive wizard. When config is missing or invalid, run the relevant wizard; block dependent work until complete.

- **Initial project setup:** When replicating the boilerplate into a new project, provide a single **initial setup wizard** (e.g. `bin/vibe setup` or `bin/setup`) that walks through all required config so nothing is left implicit.
- **Trackers:** Interactive wizard to choose Linear vs Shortcut, set API key, workspace/shortname, and required labels.
- **Branch naming:** Interactive wizard to set default format (e.g. `{PROJ}-{123}`), rename rules, milestone format (M1, M2). Block work until configured.
- **Env / secrets:** Interactive wizard for first-time env (which vars to add, allowlist), and when `.vibe/config.json` or allowlist is missing.
- **GitHub:** Interactive wizard when `gh` is not authenticated or PAT is missing (choose auth method, set PAT if needed).

---

## TICKET SYSTEM (CRITICAL)

### Primary Tracker: Linear
- Configurable adapter system
- README must include a **Shortcut recipe**
- Only one tracker active at a time

### Ticket Capabilities
Agents must be able to:
- Read / create / update / delete tickets
- Add sub-tasks
- Add blocking relationships (mandatory)
- Apply labels (comprehensive)
- Create labels (ask before creating new)
- Mark started / deployed
- Add comments (including testing instructions)

### Milestones
- Linear: ticket with `Milestone` label + required sub-tasks
- Shortcut: Epic
- Support milestone branch format (e.g. **M1**, **M2**)
- Size **L or larger**:
  - Requires ADR in `technical_docs/`
  - Must be referenced in ticket + PR
- **Ticket size:** The agent defines ticket size (S/M/L etc.) when writing or triaging tickets

### Ticket Validation (BEFORE WORK)
A ticket is **not startable** unless it has:
- Acceptance criteria
- Definition of Done
- Clear scope
If ambiguous → STOP and ask clarifying questions.

---

## WORKTREES + GIT RULES

- Every ticket → exactly one branch + worktree
- Always rebase from latest `origin/main`
- **Branch naming:** Default format is `{PROJ}-{123}` (e.g. PROJ-123). Must be renamed unless it matches the Linear workspace shortname. Configure in `.vibe/config.json` via an **interactive setup wizard**; if not set → wizard runs (block work until configured). README must explain branch naming at **ELI5** level

### Before Starting Any Ticket
1. Rebase main
2. Clean up completed worktrees
3. Detect conflicts with other active worktrees
4. If conflicts likely:
   - Add blocking relationship
   - Move ticket back to backlog

---

## PR WORKFLOW

### On PR Creation
- Open PR via GitHub
- Apply risk label:
  - Low Risk
  - Medium Risk (review recommended)
  - High Risk (review required)
- Add:
  - Entry-level testing instructions
  - Confirmation of acceptance criteria
  - Explanation of any split-off tickets
- Comment same testing instructions on the ticket

### Enforcement
- **Only applies when tests are configured to run in CI.** If tests are not in CI, do not block merge on coverage.
- High Risk PRs (when tests run in CI):
  - Must have unit test coverage if tests exist
  - Block merge otherwise
- If tests don’t exist:
  - Warn
  - Include copy-paste test proposals

---

## CI / SECURITY (DAY ONE)

Enable immediately:
- Secret scanning
- Dependency scanning
- Minimal permissions
- SBOM generation
- Gitleaks or equivalent

Create GitHub Issues **in this repo** (the boilerplate repo) as a backlog of boilerplate improvements:
- Full Shortcut integration
- Supabase support
- BYO Postgres
- Pre-commit hooks
(Define how: e.g. script, manual checklist, or GHA that runs in this repo only.)

---

## BOILERPLATE REPO ISSUES (FEEDBACK LOOP)

Every project built from this boilerplate must have the **native ability** to open and file issues in the boilerplate repo. This enables agents to report broken or inconsistent boilerplate content without the user having to ask.

**Canonical URL:** `https://github.com/kdenny/vibe-code-boilerplate/issues`

**Requirements:**
- **Config:** `.vibe/config.json` must include a `boilerplate` object with `issues_url` set to the canonical URL above (so projects know where to report).
- **Command:** A `vibe boilerplate-issue` (or equivalent) command that opens the boilerplate repo’s **new issue** page in the browser. It must accept optional `--title` and `--body` so an agent can pre-fill the issue (e.g. from a template). If the environment cannot open a browser, print the URL (with optional query params for title/body).
- **Agent rule (no user prompt required):** When you find something **broken, inconsistent, or misleading** in:
  - **CLAUDE.md** (or the project’s main agent contract file; filename must be all caps), or
  - **Any file under `recipes/`**
  you must **automatically** open or file an issue in the boilerplate repo. Include: what is broken, where (file + section or recipe path), and optional suggested fix. Do **not** wait for the user to ask; do this as part of fixing or working around the problem.

---

## ENV + SECRETS

- `.env.example` is committed
- `.env.local` is generated automatically
- Public vars → `.env.example`
- Secrets → `.env.local` only

### Secret Syncing
- Use allowlist (`.vibe/secrets.allowlist.json`)
- Provider-specific commands:
  - `vibe secrets push github`
  - `vibe secrets push vercel`
  - `vibe secrets push fly`
- Never push unallowlisted secrets

---

## DOCTOR COMMAND

`bin/doctor` must:
- Validate local setup
- Validate tickets vs config
- Validate env vars
- Validate CI / deploy config
- Work for **whatever environments are configured** (e.g. local, staging, production)
- **Stay aware as new environments are added** — do not hardcode a fixed list; doctor should validate any env that appears in config
- When validation fails, **prompt to run the relevant setup wizard** (or the initial setup wizard) rather than only printing errors

---

## README.md REQUIREMENTS (ELI5)

README must include:
- What this repo is
- When to use it
- Example usage:
  > “Make me a movie recommendation app using React + Next + OpenAI API. Use this repo as a boilerplate.”
- Step-by-step setup
- **All required setup is done via interactive wizards** — document and list them: initial setup, tracker, branch naming, env/secrets, GitHub. Step-by-step setup should refer to these wizards.
- **Branch naming:** Explain at **ELI5** level (default `{PROJ}-{123}`, when to rename, milestone format M1/M2, interactive wizard)
- Script reference
- Workflow diagrams (ASCII ok)
- Copy-paste recipe blocks at bottom

Tone: **friendly, explicit, zero assumed knowledge**

---

## CLAUDE.md REQUIREMENTS (AGENT CONTRACT)

The agent contract file must be named **CLAUDE.md** (all caps) in the project root so Cursor and other tools load it. It must:
- Mirror `.vibe/config.json`
- Explicitly state:
  - When to ask questions
  - When to block
  - How to handle ambiguity
  - How to manage tickets
  - How to clean up worktrees
  - How to open PRs
  - How to parse GHA results
- Document **all labels** and update them as they evolve
- **Boilerplate feedback:** Include the boilerplate repo issues URL (`https://github.com/kdenny/vibe-code-boilerplate/issues`) and the rule: when you find something broken or inconsistent in CLAUDE.md or any file under `recipes/`, automatically file an issue there (e.g. via `vibe boilerplate-issue --title "..." --body "..."`) without waiting for the user to ask.

Tone: **authoritative, unambiguous**

---

## FINAL OUTPUT EXPECTATION

Produce:
- All files listed
- Fully populated docs
- Working scripts (even if stubbed)
- Clear extension points
- No TODOs that hide complexity (i.e. no TODOs that *replace* necessary implementation or obscure what’s missing; TODOs that explain what’s needed are fine)

This boilerplate should feel like:
> “A calm, opinionated senior engineer who never forgets rules, never rushes, and never lets agents screw things up.”
