# Packaged Vibe — Publish Package (v0)

> **Status: canonical milestone reference (VIBE-88).** This is the single
> front-door for the **Publish Package** milestone: what v0 of the private `vibe`
> package *is*, how to develop and release it, how to consume and upgrade it from
> a downstream repo, the Claude Code DX it sets the pattern for, and what is
> deliberately **not** in v0.
>
> It **consolidates and routes to** the five source-of-truth docs produced by the
> milestone — it restates the essentials so a new engineer can read this top to
> bottom, and links each section to the precursor that owns the binding detail.
> Where this doc and a precursor disagree, **the precursor wins**; open an issue so
> this front-door is corrected.

| Area | Owned by | Source of truth |
|---|---|---|
| Package surface, core/integration boundary, config model, CLI contract, stability promise | VIBE-84 | [`package-contract.md`](package-contract.md) |
| uv build/test/release workflow, lockfiles, version bump | VIBE-85 | [`release.md`](release.md) |
| Private distribution path + downstream update/rollback contract | VIBE-87 | [`distribution.md`](distribution.md) |
| Integration module skeleton + decoupling guardrail | VIBE-86 | [`integration-skeleton.md`](integration-skeleton.md) |
| Claude Code integration-configuration DX + conventions | VIBE-179 | [`integration-dx.md`](integration-dx.md) |

The milestone is bracketed by the **VIBE-83 wall** (contract set) and the
**VIBE-89 gate** (real publish + clean install of `0.1.0`). This doc is the
reference both bracket against.

---

## 1. Goals & non-goals (v0)

**Goal:** turn `vibe` into a **versioned, private upstream package** that
downstream repos (LIFT / PROMPT / DEAL) install à la carte, with **PR automation
as the first real capability** shipped behind the package seam.

**v0 is intentionally narrow and opinionated.** It proves the *rails* — surface,
packaging, distribution, DX — end to end on one capability, rather than shipping a
broad provider catalog.

| In scope for `0.1.0` | Deferred (documented direction, **not built**) |
|---|---|
| One private package; dist name **and** import package both `vibe`; `uv` as the default workflow | Standalone binary / CLI-wrapper install path |
| **PR automation** capability + CLI + Claude Code DX behind the integration seam | The four-module taxonomy (`linear`/`neon`/`axiom`/`flyio`) as first-class modules |
| Injected typed config **+** optional `.vibe/` loader | Floating semver channels (`~=0.1`) across many repos |
| Private **git-tag + uv** distribution; explicit-pin update contract | A private package index / wheel-hosting infra |
| Public, stable import + CLI + config surface (the VIBE-84 stability promise) | Public PyPI distribution |

> The PR-automation **engine** itself is M2 (VIBE-128/129). v0 ships the **seam,
> the reference skeleton, the config/telemetry contract, and the packaging** the
> engine plugs into — not the production runner.

---

## 2. What ships in `0.1.0` (and what's deferred)

### 2.1 v0 module inventory (shipped)

- **`vibe` core** — config model + `.vibe/` loader, CLI dispatch + verb registry,
  the public error hierarchy, and the **integration registration seam**. Core
  ships with **zero provider dependencies**.
- **`vibe.integrations.pr_autopilot`** — the **reference integration skeleton**:
  `PRAutopilotConfig` + `integration`, pre-engine operator verbs (`configure`,
  `status`, `inspect`, `enable`, `disable`) that run in bare core, an
  engine-gated `run` verb, and the **PR Autopilot run-telemetry contract**
  (`PRAutopilotRunTelemetry`, `PRAutopilotTelemetryEvent`, `JsonlTelemetrySink`,
  `LinearTelemetrySink`).
- **The CLI** — `vibe` console script + `python -m vibe`, the
  `vibe <integration> <verb>` tree, reserved core verbs (`status`, `version`,
  `doctor`), and the public `vibe.cli.{Integration, verb, register}` registry API.
- **The owned `.vibe/` artifact** — layered, reviewable desired-state config with
  secret *references* (never values).
- **Packaging + release rails** — `pyproject.toml` (`setuptools.build_meta`),
  `uv.lock` + `requirements.lock`, the `Release` GitHub Actions workflow, and
  private git-tag distribution.

### 2.2 Future taxonomy (direction, NOT built in v0)

The four-module set — `linear`, `neon`, `axiom`, `flyio` — is **documented
direction only**. The namespace is built to absorb it without a reshuffle: a
future "module" is just a `vibe.integrations.<name>` with a richer surface,
registered the same way as `pr_autopilot`. No v0 code implements these as
first-class modules; do not treat their mention as shipped scope. (See
[`package-contract.md`](package-contract.md) §1.2, §9.)

---

## 3. The package contract (summary of VIBE-84)

Full spec: [`package-contract.md`](package-contract.md).

- **Import surface.** `vibe`, `vibe.config`, `vibe.cli` (registry API only),
  `vibe.errors.*` are **stable across downstream repos**. Each integration is
  imported only through `vibe.integrations.<name>.{integration, <Name>Config}` —
  everything else under an integration is internal.
- **Core ↔ integration boundary.** Core owns config, CLI, errors, and the
  registration seam; integrations own provider schema, provider verbs, and
  provider I/O. **Core never imports an integration** — discovery is one-way via
  the seam. A guardrail test fails on app-code imports
  (`tests/test_integrations_guardrails.py`).
- **Config model.** Typed, frozen, injected config objects, optionally
  materialized from `.vibe/config.toml` (shared identity) +
  `.vibe/<integration>.toml` (**presence = enablement**). **Secrets are
  references** (`gh:` / `env:` / `op:`), resolved at runtime, never written back.
  Precedence: **explicit (injected) > environment > file**.
- **CLI contract.** `vibe <integration> <action>`; `--json` on read verbs
  (machine output → stdout, narration → stderr); `vibe status` **reconciles**
  desired vs. real state and exits non-zero on drift; slash commands under
  `.claude/commands/` are **thin wrappers** with no business logic.
- **Extras semantics.** Provider deps live in an extra named for the integration
  slug (`vibe[pr-autopilot]`). Bare `vibe` is core-only; invoking an integration
  whose extra is missing raises an actionable `MissingExtraError`, not a traceback.
- **Public error hierarchy.** `VibeError` → `ConfigError`, `MissingExtraError`,
  `SecretResolutionError`, `IntegrationError`. These names are **stable**.

---

## 4. Develop & release with uv (summary of VIBE-85)

Full procedure: [`release.md`](release.md).

| Concern | Value |
|---|---|
| Distribution / import name | `vibe` / `vibe` |
| Build backend | `setuptools.build_meta` |
| Runtime Python | `>=3.11` |
| Version source | `VERSION` (SemVer) |
| Release tag | `vMAJOR.MINOR.PATCH` matching `VERSION` |
| Lockfiles | `uv.lock` (default), `requirements.lock` (pip fallback) |

**Develop (fresh checkout):**

```bash
UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --group dev --extra pr-autopilot
export PATH="$PWD/.venv/bin:$PATH"
```

**Validate before pushing:** `bin/ci-local` (full) or `bin/ci-local --fast`
(inner loop). After changing deps in `pyproject.toml`, regenerate **both** locks
in the same PR (`uv lock` + `uv pip compile … -o requirements.lock`).

**Release** is gated by the `Release` GitHub Actions workflow: it verifies
`VERSION` ↔ tag ↔ `CHANGELOG.md` agreement, runs `bin/ci-local --fast`, builds
wheel + sdist with `uv build`, and — on `dry_run=false` — **creates and pushes an
annotated, immutable `vX.Y.Z` tag**. The tag *is* the published artifact for v0.
Bump with `vibe bump patch|minor|major` and add a matching `## <version>`
`CHANGELOG.md` section before release.

---

## 5. Consume & update (summary of VIBE-87)

Full contract: [`distribution.md`](distribution.md).

**Distribution path (v0 decision): git tag + `uv`.** A downstream repo depends on
`vibe` as a **git dependency pinned to an annotated tag**, resolved and locked by
`uv`. No package index, no wheel hosting, **no new secret** beyond what cloning a
private repo already needs.

```toml
# downstream pyproject.toml
[project]
dependencies = ["vibe[pr-autopilot]"]

[tool.uv.sources]
vibe = { git = "https://github.com/kevin-earl-denny/vibe-code-boilerplate", tag = "v0.1.0" }
```

```bash
uv sync   # resolves + pins the exact commit into uv.lock; reproducible
```

**Auth per consumer:** CI uses the PR-autopilot GitHub App token / `GITHUB_TOKEN`
as the git credential; the self-hosted `fly-ephemeral` runner bakes/injects the
same; friend repos use the `git+ssh` form with an existing key; local dev uses
existing `gh auth`. No token value is ever committed.

**Update / rollback contract:**

- **Explicit pins only** for v0 — a downstream repo never moves versions without a
  reviewable `pyproject.toml` + `uv.lock` diff. Upgrade =
  `uv lock --upgrade-package vibe && uv sync` after bumping the tag.
- **Rollback is symmetric** — restore the prior tag, re-lock, commit. Published
  tags are **immutable**; a bad release is superseded by a new tag, never rewritten.
- **No vendored copy.** Downstream consumes `vibe` only as the git dependency; the
  dependency edge *is* the sync mechanism, so there is nothing to drift. The
  `CHANGELOG` is the single place to learn what a tag changed.

**Flip-points (when to revisit the path):** external consumers who aren't repo
collaborators → reconsider a private index; git-clone time dominating runner
cold-start → adopt a GitHub Releases wheel (a strict, GitHub-only, additive
upgrade); a need for true floating semver channels → reconsider a private index.

---

## 6. The Claude Code DX (summary of VIBE-179)

Full prototype contract: [`integration-dx.md`](integration-dx.md); reference
skeleton: [`integration-skeleton.md`](integration-skeleton.md).

**Thesis:** in Claude Code the **agent is the operator** and the human is the
approver / value-provider. Vibe **owns the seams** — the reviewable `.vibe/`
desired-state artifact, secret *references* not values, status/drift
reconciliation, and crisp human handoffs for anything only a human can provide
(a secret, a login, billing, a subjective call). Vibe **does not re-skin
providers** — Claude still shows `gh` / `flyctl` / `neonctl` / provider API calls
in the transcript.

**Reusable command shape** (every integration exposes the same verbs through the
VIBE-84 registry):

```bash
bin/vibe <integration> configure   # safe to rerun; infer → confirm → write → handoff → "run status next"
bin/vibe <integration> status      # configured? enabled? authed? healthy? drifted? next?
bin/vibe <integration> inspect
bin/vibe <integration> enable
bin/vibe <integration> disable
bin/vibe status                    # summarizes every configured integration
```

**PR automation is wired first** as the reference: the operator verbs work in bare
core today; `run` stays gated by the `pr-autopilot` extra until the M2 engine
lands. The **telemetry contract** behind the seam (VIBE-146) requires every run to
emit one `pr_autopilot.run.started` and exactly one terminal event —
`completed` (success), `failed` (failure), or `timed_out` (timeout) — with failed
and timed-out events **visible in Linear first** for human triage; Axiom/other
sinks are secondary subscribers to the same structured events.

This is the pattern every future integration follows.

---

## 7. Known risks & deferred work

- **Scope creep into the four-module taxonomy.** The biggest risk is treating the
  documented `linear`/`neon`/`axiom`/`flyio` direction as v0 scope. It is **not**
  — v0 ships PR automation only (§2.2). Guard the line in review.
- **Repo-local assumptions leaking upstream.** An integration that imports app/repo
  code (`app`, `src`, `lift`, `deal`) or assumes a repo layout breaks downstream
  consumption. The decoupling guardrail test
  (`tests/test_integrations_guardrails.py`) is the enforcement; keep it green.
- **Binary-path deferral.** v0 has no standalone binary / CLI-wrapper install;
  consumers need a Python ≥3.11 + `uv` (or pip) environment. Revisit only if a
  no-Python consumer appears.
- **Cold-install time on the runner.** git-clone install may dominate
  `fly-ephemeral` cold-start; the documented mitigation is the GitHub Releases
  wheel flip-point (§5), adopted **only** if measured to matter.
- **Engine is not yet here.** `pr_autopilot.run` is a gated skeleton until
  VIBE-128/129. Downstream should not depend on engine behavior before then —
  only on the **config + CLI + telemetry contract** this milestone fixes.

---

## 8. Downstream migration notes (LIFT / PROMPT / DEAL pilots)

For a downstream repo adopting packaged `vibe`:

1. **Pin, don't vendor.** Add `vibe[pr-autopilot]` to `pyproject.toml` and pin the
   tag in `[tool.uv.sources]` (§5). Never copy `vibe` source into the repo — the
   git dependency edge is the sync mechanism.
2. **Own a `.vibe/` artifact.** Commit `.vibe/config.toml` (shared identity) and a
   `.vibe/<integration>.toml` per enabled integration. The artifact is
   **version-independent config** — upgrading `vibe` does not require regenerating
   it, because config keys are part of the stability promise. Use **secret
   references**, never values.
3. **Drive it from Claude Code.** `bin/vibe <integration> configure` then
   `bin/vibe status`; the agent runs the provider's native tools and hands off to
   a human only for secrets/logins/billing/subjective calls (§6).
4. **Upgrade deliberately.** Bump the tag, `uv lock --upgrade-package vibe &&
   uv sync`, read the `CHANGELOG`, commit the lock diff. Rollback is symmetric.
5. **Expect the engine later.** Build against the **contract** (import paths, CLI
   verbs, config keys, telemetry events), which is stable; the PR-automation
   runner itself arrives with the M2 engine, behind the same seam.

For the per-provider milestone shape these pilots will reuse, see
[`docs/review/external-service-milestone-pattern.md`](../review/external-service-milestone-pattern.md).

---

## Consistency check (acceptance criteria)

- **Exists in-repo and internally consistent** with VIBE-84/85/86/87/179 — every
  section restates its precursor and links to it as the binding source. ✅
- **A new engineer can read it** and learn what to install (§4–5), how to consume
  `vibe` (§5–6), and what is intentionally not in v0 (§1–2, §7). ✅
- **Future-taxonomy and deferred work are clearly separated** from shipped v0
  scope (§1 table, §2.2, §7). ✅
