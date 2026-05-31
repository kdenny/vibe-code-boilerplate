# Cloud-fast repo bootstrap (warm/cold contract)

How a cold checkout of VIBE gets to a green `bin/ci-local` fast enough that a
cloud coding agent spends its loop on the task, not on setup. This is the
**speed rule** from [`CLAUDE.md`](../../CLAUDE.md) applied to the bootstrap path,
and the concrete deliverable of VIBE-185 (parent goal VIBE-140; agent selection
in [`ADR-001`](../../docs/decisions/ADR-001-cloud-coding-agent-selection.md)).

## The contract

| Phase | What it means | Target | What pays for it |
|-------|---------------|--------|------------------|
| **Cold** | Fresh clone, empty dep cache → deps installed → `bin/ci-local` green | **< 60s** | pinned `requirements.lock` + uv |
| **Warm** | Dep cache restored (volume / CI cache) → scoped `bin/ci-local --scope` green | **< 10s** | restored uv cache + module-scoped pytest |

"Warm" is the steady state of an agent loop: the dependency cache is already on
the volume, so install is near-instant and the only real cost is the *scoped*
test run for the files the agent just touched.

## The two levers

### 1. Pinned, cacheable install — `requirements.lock`

`requirements.lock` is the fully-pinned, hash-locked closure of the runtime +
`dev` dependencies, generated from `pyproject.toml`. It is the single artifact
the dependency cache is keyed on, and **both uv and pip install from it
identically** — so the fast path and the fallback resolve to the same versions.

```bash
# Fast path (preferred): uv, hash-verified
uv pip sync requirements.lock          # exact locked closure
uv pip install -e . --no-deps          # + the editable project (deps already locked)

# Fallback (no uv): plain pip, same lock, same hashes
pip install -r requirements.lock
pip install -e . --no-deps
```

Regenerate the lock whenever you change dependencies in `pyproject.toml`
(this is a contract change — it forces the full test suite, see below):

```bash
uv pip compile pyproject.toml --extra dev --generate-hashes -o requirements.lock
```

### 2. Module-scoped validation — `bin/ci-local --scope`

A warm loop doesn't re-run 800+ tests for a one-file change. `bin/ci-local
--scope` pipes the changed files through `vibe/testscope.py` (the same
selector `.github/workflows/tests.yml` uses — one source of truth) and runs only
the affected suites. See [`recipes/testing/modular-testing.md`](../testing/modular-testing.md)
for the selection rules and when a full-tree run is still required.

## The cache key

Restore/save the dependency cache on this key:

```text
hash(requirements.lock) + python-version + runner-os
```

- **GitHub Actions:** handled by `astral-sh/setup-uv` with `enable-cache: true`
  and `cache-dependency-glob: requirements.lock` (it also folds in the uv
  version and runner OS). When the lock is unchanged, the install is a cache
  restore, not a download.
- **Cloud runner (Fly volume / Cursor cache):** persist uv's cache directory
  (`$UV_CACHE_DIR`, default `~/.cache/uv`) on the volume, keyed on the lock
  hash. A new task with an unchanged lock reuses it; a lock change invalidates
  it and triggers one cold re-download.

The key is deliberately the lock **content hash**, not a timestamp or branch:
two checkouts with the same `requirements.lock` share a cache, and the only
thing that busts it is an actual dependency change.

## Measured baseline (record per-PR; these are the VIBE-185 numbers)

Apple M-series, Python 3.13. Numbers move with hardware/runner; the **shape** is
the point — uv + lock + scope turn a ~45s cold full run into a ~2s warm scoped
loop.

| Step | pip (baseline) | uv + lock (this change) |
|------|----------------|--------------------------|
| Cold install (empty cache) | ~13.8s | ~5.7s |
| Warm install (cache present) | — | ~1.3s |
| `bin/ci-local` full suite | ~44.5s (809 tests) | ~44.5s (unchanged) |
| `bin/ci-local --scope` one module | n/a | **~2.2s** |

**Cold budget:** uv cold install (~6s) + full `bin/ci-local` (~45s) ≈ **~51s < 60s**.
**Warm budget:** warm install (~1.3s) + scoped `bin/ci-local --scope` (~2s) ≈ **~3s < 10s**.

> Local stays the source of truth: `bin/ci-local` with no flag runs the **full**
> suite. `--scope` is the fast warm-loop path; the full suite is the backstop on
> `main` and before anything ships.
