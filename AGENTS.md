# AGENTS.md

Guidance for autonomous agents (including Cursor Cloud) working in this repository.

> **Relationship to CLAUDE.md (read this).** [`CLAUDE.md`](CLAUDE.md) is the
> **canonical contract** (the rules, the why, the architecture). This file is its
> **agent-facing operational mirror** — the fast, do-this-now quickstart an agent
> reads from the checkout. The two are a matched set under CLAUDE.md standing rule
> #1: this file must never contradict CLAUDE.md, and a change to the PR policy,
> the run/validation flow, or the agent-PR contract updates **both** in the same
> PR. When in doubt, CLAUDE.md wins.

## Starting a ticket

- **Mark the ticket In Progress the moment you start it.** `bin/vibe do <ticket>` does this automatically (it moves the ticket into the team's active workflow state). If you begin work some other way — picking up an existing worktree, or a path that didn't run `do` — set it yourself: `bin/ticket update <ticket> --status "In Progress"`. The board is an agent execution queue; a ticket that's being worked must *say* so, or two agents collide on it.

## Pull requests (agent default)

- **Open PRs ready for review** (`draft: false`), and **always base on `main`** — never on another feature branch. Open a draft only when the work **depends on a not-yet-merged PR**: base it on `main` anyway, label it **`DNM`**, note the dependency in both the PR and the ticket, and once the parent lands rebase onto `main`, drop `DNM`, and mark ready. A PR based on a feature branch is never a valid final state.
- **Metadata:** title `VIBE-<n>: …`, one of **Low / Medium / High Risk**, and a description that satisfies the agent-PR contract in [`CLAUDE.md`](CLAUDE.md) (test proof, staged step when applicable, sync confirmation).
- **CodeRabbit:** treat approval as the merge gate — run `bin/ci-local` locally first, fix anything CodeRabbit flags, and push again. Agents cannot click “approve” on CodeRabbit’s behalf; keep the PR green and address review comments until CodeRabbit approves or a human overrides.

## Cursor Cloud specific instructions

> **Setup is automated.** [`.cursor/environment.json`](.cursor/environment.json)
> runs the install below on every Cloud-agent boot, and the human-side controls
> (branch-only token, secret store, spend cap, kill switch, no-auto-merge gate)
> are documented in
> [`docs/operations/cursor-cloud-agents-runbook.md`](docs/operations/cursor-cloud-agents-runbook.md).
> The manual steps here are the same commands, for reference / non-Cursor agents.

### What this repo is

VIBE is a **Python CLI toolkit** (`bin/vibe`, `bin/ticket`, `bin/ci-local`, …) plus `lib/vibe/`. There is **no** long-running web app or `docker compose` stack to start. Development = install deps, run CLIs, validate with `bin/ci-local`.

Canonical bootstrap contract: [`recipes/environments/cloud-bootstrap.md`](recipes/environments/cloud-bootstrap.md).

### Dependency install (preferred)

Python **≥ 3.11** required. Use the pinned lockfile and **uv** when available
(this mirrors the `install` step in `.cursor/environment.json`):

```bash
# One-time on a fresh VM if uv is missing:
command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

test -d .venv || uv venv .venv
UV_PROJECT_ENVIRONMENT=.venv uv pip sync requirements.lock
UV_PROJECT_ENVIRONMENT=.venv uv pip install -e . --no-deps
export PATH="$PWD/.venv/bin:$PATH"
git config core.hooksPath .githooks   # activate the pre-push lint/mypy gate
```

**Why `core.hooksPath`:** the `.githooks/pre-push` hook runs ruff + mypy before a
push reaches CI. It only fires once `core.hooksPath` points at `.githooks` —
`.cursor/environment.json` sets this automatically; set it by hand on a manual
clone. `bin/ci-local` and the hook both auto-resolve tools from `.venv/`/`.direnv/`
even when the venv is not on `PATH`, so a missing-from-`PATH` mypy can no longer
silently skip — it either runs or warns **loudly**.

Fallback (no uv): `pip install -r requirements.lock` then `pip install -e . --no-deps`.

`bin/vibe` uses its own `.vibe/.venv/`; on Debian/Ubuntu install **`python3.12-venv`** (or matching version) if `bin/vibe doctor` fails creating a venv.

### Validation

| Goal | Command |
|------|---------|
| Full local CI (source of truth) | `unset LINEAR_API_KEY` then `bin/ci-local` |
| **Before every push** (lint + mypy) | `bin/ci-local --fast` |
| Fast warm loop (module-scoped) | `bin/ci-local --scope lib/vibe/<module>.py` |
| Predict CI pytest scope | `PYTHONPATH=. python3 -m lib.vibe.testscope <paths>` |

**Run `bin/ci-local --fast` before you push.** It runs ruff + mypy + scoped
tests in seconds and is the same gate the `.githooks/pre-push` hook enforces. If
either prints a loud `⚠ … SKIPPED` warning, a core linter did **not** run
(usually the venv isn't installed) — CI will still fail you; install the tools
and re-run. Never push past a skip warning.

**`LINEAR_API_KEY`:** Cloud VMs often inject this secret. One unit test (`test_authenticate_no_api_key`) expects no key — **unset `LINEAR_API_KEY` before `bin/ci-local`** unless you are doing live Linear work.

**Scoped vs full:** Changes under shared/core paths (`config`, `config_schema`, `env`, `utils/`, `pyproject.toml`, `lib/vibe/testscope.py`, …) intentionally run the **full** pytest suite via `--scope`. That matches CI.

### Running the “application”

Use the CLIs directly (with `.venv/bin` or `bin/` on `PATH`):

```bash
bin/vibe doctor          # health check (no live APIs)
bin/vibe setup --quick   # first-time config; may prompt for GitHub dependency graph (answer n in non-interactive)
bin/vibe version
```

Live tracker/API flows need credentials in `.env.local` (gitignored); not required for pytest or doctor.

### Lint / test shortcuts

Same tools as `bin/ci-local`: `ruff check .`, `ruff format . --check`, `mypy lib/vibe/`, `pytest`. See [`CLAUDE.md`](CLAUDE.md) validation contract table.

### Optional integrations

GitHub (`gh`), Linear, Slack, etc. are **optional** for automated tests. Do not block setup on them unless the task requires live API calls.
