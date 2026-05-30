# AGENTS.md

Guidance for autonomous agents (including Cursor Cloud) working in this repository.

## Pull requests (agent default)

- **Open PRs ready for review** (`draft: false`). Do **not** open draft PRs unless the user explicitly asks and the work is **stacked on another feature branch** that has not merged to `main` yet — those PRs must be labeled **`DNM`** until the parent lands, then rebase onto `main`, drop `DNM`, and mark ready.
- **Metadata:** title `VIBE-<n>: …`, one of **Low / Medium / High Risk**, and a description that satisfies the agent-PR contract in [`CLAUDE.md`](CLAUDE.md) (test proof, staged step when applicable, sync confirmation).
- **CodeRabbit:** treat approval as the merge gate — run `bin/ci-local` locally first, fix anything CodeRabbit flags, and push again. Agents cannot click “approve” on CodeRabbit’s behalf; keep the PR green and address review comments until CodeRabbit approves or a human overrides.

## Cursor Cloud specific instructions

### What this repo is

VIBE is a **Python CLI toolkit** (`bin/vibe`, `bin/ticket`, `bin/ci-local`, …) plus `lib/vibe/`. There is **no** long-running web app or `docker compose` stack to start. Development = install deps, run CLIs, validate with `bin/ci-local`.

Canonical bootstrap contract: [`recipes/environments/cloud-bootstrap.md`](recipes/environments/cloud-bootstrap.md).

### Dependency install (preferred)

Python **≥ 3.11** required. Use the pinned lockfile and **uv** when available:

```bash
# One-time on a fresh VM if uv is missing:
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

uv venv .venv
UV_PROJECT_ENVIRONMENT=.venv uv pip sync requirements.lock
UV_PROJECT_ENVIRONMENT=.venv uv pip install -e . --no-deps
export PATH="/workspace/.venv/bin:$PATH"
```

Fallback (no uv): `pip install -r requirements.lock` then `pip install -e . --no-deps`.

`bin/vibe` uses its own `.vibe/.venv/`; on Debian/Ubuntu install **`python3.12-venv`** (or matching version) if `bin/vibe doctor` fails creating a venv.

### Validation

| Goal | Command |
|------|---------|
| Full local CI (source of truth) | `unset LINEAR_API_KEY` then `bin/ci-local` |
| Fast warm loop (module-scoped) | `bin/ci-local --scope lib/vibe/<module>.py` |
| Predict CI pytest scope | `PYTHONPATH=. python3 -m lib.vibe.testscope <paths>` |

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
