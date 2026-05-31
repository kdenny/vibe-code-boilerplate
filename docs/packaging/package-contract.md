# Packaged Vibe — Package Surface & Module Taxonomy (v0 Contract)

> **Status: v0 architectural contract (VIBE-84).** This document is the spec the
> rest of the Publish Package milestone implements. It ships **no feature code** —
> it names the public surface so VIBE-85 (packaging/release), VIBE-86 (plugin
> seam), VIBE-179 (DX prototype), VIBE-141 (external-service pattern), VIBE-182,
> and M2's VIBE-128/129 can all be built from it without further architectural
> decisions.
>
> Grounded in the **VIBE-83 wall** (injected core + optional loader) and the
> **VIBE-179 DX thesis** (the agent is the operator; the owned `.vibe/` artifact is
> the whole ballgame). Where this doc and VIBE-179 describe the same decision from
> two sides (artifact vs. loader), they are the same decision.

---

## 0. Naming note — target vs. current

VIBE-182 moved the repository to the v0 import package (`vibe`) and console
entrypoint (`vibe.cli.main:main`). The distribution name is still
`vibe-boilerplate` until VIBE-85 finalizes the release/build mechanics:

| | After VIBE-182 | v0 target (this contract) |
|---|---|---|
| Distribution name | `vibe-boilerplate` | `vibe` |
| Import package | `vibe` | `vibe` |
| Console script | `vibe = vibe.cli.main:main` | `vibe = vibe.cli.main:main` |
| Build backend | setuptools | finalized by VIBE-85 |

VIBE-85 now builds against the existing `vibe` package skeleton instead of
performing a code move.

> **VIBE-86 implementation note:** the registration seam now exists in the current
> package as `vibe.cli.{Integration, verb, register}` and
> `vibe.integrations.*`, with entry points in the `vibe.integrations` group.
> VIBE-182 re-homed these paths to `vibe.*`; the names, CLI slug rules, extras
> semantics, and decoupling guardrails are the v0 target shape.

---

## 1. Import surface

### 1.1 Stable top-level

```python
import vibe                      # package root — stable
from vibe import config          # typed config model + loader (§3)
from vibe import cli             # CLI dispatch + verb registry (§5)
from vibe.errors import ...      # the public exception hierarchy (§6.1)
```

`vibe` (top-level) is **stable across downstream repos** for v0. Anything reachable
without a leading underscore from `vibe`, `vibe.config`, `vibe.errors`, and the
documented integration entrypoints is part of the promise (§7).

### 1.2 Integration submodule convention

Integrations live under a single, predictable namespace:

```text
vibe.integrations.<name>          # canonical location for every integration
```

`<name>` is the integration's stable slug (`pr_autopilot`, `linear`, `neon`,
`axiom`, `fly`, …). Each integration module exposes exactly two public symbols — its
**registration entrypoint** `integration` (§4) and its **typed config class** (§3.1),
which downstream constructs directly for the injected path:

```python
from vibe.integrations.pr_autopilot import integration         # an Integration instance
from vibe.integrations.pr_autopilot import PRAutopilotConfig    # its typed config class
```

Everything else inside `vibe.integrations.<name>.*` is **internal** and may change
without a major bump. Downstream code imports the integration through these two
symbols (and its registered verbs/config), never by reaching into its internals.

> **Why `vibe.integrations.<name>` and not `vibe.<name>`:** it keeps the top-level
> namespace small and stable, makes "what is an integration" answerable by listing
> one package, and matches the à-la-carte enablement model (`ls .vibe/*.toml` ↔
> `vibe.integrations.*`). The current repo's flat subpackages (`vibe.trackers`,
> `vibe.secrets`, `vibe.costs`, …) collapse into this namespace during the
> VIBE-86 move.

### 1.3 Public vs. internal — the rule

- **Public:** `vibe`, `vibe.config`, `vibe.errors`, `vibe.cli` (the registry API
  only — see §5.4), and each integration's `integration` object + its declared
  config schema, CLI verbs, and entrypoints.
- **Internal (no stability promise):** any name prefixed `_`, anything under
  `vibe.integrations.<name>.*` other than `integration`, and `vibe._internal.*`.

---

## 2. Core vs. integration boundary

| Concern | Lives in `vibe` **core** | Lives in an **integration** |
|---|---|---|
| Config model + loader (`.vibe/` read, precedence, secret-ref resolution) | ✅ | — |
| CLI dispatch, verb tree, help/output conventions, `vibe status` engine | ✅ | — |
| Logging, shared types, the public error hierarchy | ✅ | — |
| The **registration seam** (`Integration`, registry, discovery) | ✅ | — |
| Provider-specific config *schema* (what keys this integration needs) | — | ✅ |
| Provider CLI verbs (`vibe pr-autopilot run`) + their handlers | — | ✅ |
| Desired-state → reconcile logic feeding `vibe status` | core engine | per-integration *check* |
| Talking to the provider (`gh`, `flyctl`, Linear API, Axiom API) | — | ✅ |

**Core never imports an integration.** Dependency points one way: integrations
depend on `vibe` core; core discovers integrations only through the registration
seam (§4). This is the guardrail VIBE-86 enforces with a check/test.

**Core ships with zero provider dependencies.** `requests`/`click`/TOML parsing as
needed for the core loop only; every provider SDK/CLI dependency is gated behind an
extra (§6).

---

## 3. Config model + owned artifact

This section is the **loader side** of the VIBE-179 artifact thesis.

### 3.1 Typed, injected config

Core consumes **typed config objects**, one per integration, injected by the caller.
The package functions with **no `.vibe/` directory present** — injected config alone
is sufficient (this is the downstream/embedded path; the VIBE-83 "injected core"):

```python
from vibe.integrations.pr_autopilot import PRAutopilotConfig
from vibe.integrations.pr_autopilot import integration

cfg = PRAutopilotConfig(github_owner="acme", linear_team="ENG")
integration.run(cfg)            # no files read; pure injection
```

Each integration's config is a typed object (dataclass / pydantic-style — final
choice in VIBE-85, but the *shape* is fixed here: a frozen, validated value object
with explicit fields, no free-form dict).

### 3.2 The on-disk artifact (optional loader)

A thin, **optional** loader materializes typed config from the layered `.vibe/`
artifact:

```text
.vibe/config.toml            # shared identity/wiring (one file)
.vibe/<integration>.toml     # one declarative file per ENABLED integration
```

- `.vibe/config.toml` — shared identity: `github.owner`, `linear.team`,
  `axiom.default_dataset`, etc. Read by core; merged into every integration's config.
- `.vibe/<integration>.toml` — **its presence = enablement.** À-la-carte maps
  literally to `ls .vibe/*.toml`. One declarative, `fly.toml`-spirit file per
  integration stating desired state.
- **Secrets are references, never values.** A secret field holds a *reference*
  string, resolved at runtime, never a literal:

  ```toml
  # .vibe/pr_autopilot.toml
  anthropic_api_key = "gh:ANTHROPIC_API_KEY"     # GitHub Actions secret
  linear_api_key    = "env:LINEAR_API_KEY"       # process environment
  ```

  Reference schemes for v0: `gh:` (GitHub secret), `env:` (process env), `op:`
  (1Password / external secret manager — resolver pluggable). The loader **never
  writes a resolved value back to disk**; a committed `.vibe/` file is always safe
  to read.

### 3.3 Precedence

**Explicit (injected) > environment > file.**

1. A field passed directly to the typed config object wins outright.
2. Otherwise, an `env:`-resolved value (and `VIBE_<INTEGRATION>_<FIELD>` env
   overrides) applies.
3. Otherwise, the `.vibe/` file value (with its secret reference resolved).

Missing required field after all three layers → a typed `ConfigError` (§6.1) naming
the field and the integration, never a bare `KeyError`.

---

## 4. Integration / registration seam

The seam VIBE-86 implements and VIBE-128's PR-automation engine plugs into. An
integration is a single declarative object registered with core:

```python
# vibe/integrations/pr_autopilot/__init__.py
from vibe.cli import Integration, verb

integration = Integration(
    name="pr_autopilot",
    config_cls=PRAutopilotConfig,         # typed config schema (§3.1)
    verbs=[                               # CLI verbs (§5)
        verb("configure", handler=configure_handler, requires_extra=False),
        verb("status", handler=status_handler, requires_extra=False),
        verb("inspect", handler=inspect_handler, requires_extra=False),
        verb("enable", handler=enable_handler, requires_extra=False),
        verb("disable", handler=disable_handler, requires_extra=False),
        verb("run", handler=run_handler, help="Run the PR autopilot loop"),
    ],
    extra="pr-autopilot",                 # the optional-dependency extra (§6)
    check=reconcile,                      # desired-state → reality, feeds `vibe status`
)
```

- **Registration is declarative and à la carte.** Core discovers integrations via
  Python entry points (`[project.entry-points."vibe.integrations"]`, wired in
  VIBE-85) **and/or** an explicit registry call; either way an integration is
  enabled only when (a) its package/extra is installed and (b) it is registered.
- **`config_cls`** declares the schema; **`verbs`** declares the CLI surface;
  **`check`** declares how this integration reconciles against reality for
  `vibe status` (§5.3); **`extra`** ties the integration to its optional-dependency
  group so core can produce the actionable "install `vibe[...]`" error (§6).
- **`extra_module` (implementation detail)** names the importable runtime module
  used to prove the optional dependency is actually available. The PR Autopilot
  skeleton uses `vibe_pr_autopilot` until VIBE-128 supplies the real engine.
- **`requires_extra=False` (implementation detail)** lets pre-engine operator
  verbs (`configure`, `status`, `inspect`, `enable`, `disable`) run in bare core
  while engine verbs such as `run` keep the default extra gate.
- **One-way coupling.** The integration imports `Integration`/`verb` from core; core
  never imports the integration module by name. Discovery is the only edge.

---

## 5. CLI contract

### 5.1 Entrypoints

```text
vibe ...                # console_scripts entry (pyproject [project.scripts])
python -m vibe ...      # module entrypoint — identical dispatch
```

Both route through `vibe.cli.main:main`. Behavior is identical; `python -m vibe`
exists for environments where the script shim is unavailable.

### 5.2 Verb tree

```text
vibe <integration> <action> [options]
vibe status [<integration>]
vibe <core-verb> ...           # reserved core verbs (status, version, doctor)
```

- Integration verbs are namespaced under the integration slug:
  `vibe pr-autopilot run`, `vibe linear list`. (CLI uses kebab-case for the slug;
  the import name uses snake_case: `pr-autopilot` ↔ `pr_autopilot`.)
- Core reserves a small set of top-level verbs: `status`, `version`, `doctor`.
  Integrations may not shadow them.

### 5.3 `vibe status` — reconcile, don't just report

`vibe status` walks every enabled integration (`ls .vibe/*.toml`), runs its
declared `check`, and reports, per integration: **configured? authed? enabled?
healthy? drifted?** This is the Fly-model desired-state reconciliation from
VIBE-179 Principle 5. `vibe status <integration>` scopes to one. Exit code is
non-zero on drift so it is usable as a gate.

### 5.4 Help, output, and the registry API

- Every verb has one-line help; `vibe`, `vibe <integration>`, and
  `vibe <integration> --help` all list their children.
- Output is human-first but **`--json` is available on read verbs** (`status`,
  `list`-style) for agent consumption. Machine output goes to stdout; narration/logs
  go to stderr.
- The **public registry API** (`vibe.cli.Integration`, `vibe.cli.verb`, and the
  function that registers an `Integration`) is the only part of `vibe.cli` that is
  stable; the dispatch internals are not.

### 5.5 Claude Code slash-command wrapping

Slash commands under `.claude/commands/` are **thin wrappers** over the `vibe` CLI
(VIBE-179 deliverable 1): they shell out and *show* the native tool running; they
contain **no business logic**. The CLI is the contract; the markdown is a shortcut.

---

## 6. Optional-dependency / extras semantics

- An integration's provider dependencies live in an extra named for the integration:
  `vibe[pr-autopilot]`, `vibe[linear]`, `vibe[fly]`, … (declared in `pyproject.toml`
  by VIBE-85; this contract fixes the *naming* = the integration slug).
- Installing bare `vibe` gives **core only**. Importing or invoking an integration
  whose extra is not installed yields a **clear, actionable error**, not a traceback:

  ```text
  $ vibe pr-autopilot run
  Error: integration 'pr-autopilot' requires its extra.
         Install it with:  uv pip install 'vibe[pr-autopilot]'
  ```

  Implemented as a `MissingExtraError` (§6.1) raised at the registration/dispatch
  boundary when the integration's declared `extra` is not importable. This is the
  guardrail-visible behavior VIBE-86 asserts in a test.

### 6.1 Public error hierarchy

```text
vibe.errors.VibeError                 # base — everything catchable here
├── ConfigError                       # missing/invalid config field (§3.3)
├── MissingExtraError                 # integration used without its extra (§6)
├── SecretResolutionError             # a secret reference could not be resolved
└── IntegrationError                  # provider-side failure (wraps the cause)
```

These names are **stable** (§7). Integrations raise `IntegrationError` (or a
subclass) for provider failures so downstream callers have one catchable base.

---

## 7. Stability promise (v0)

**Stable across downstream repos — changing these is a breaking change:**

- Import paths: `vibe`, `vibe.config`, `vibe.errors.*`, `vibe.cli.{Integration,verb,register}`,
  and `vibe.integrations.<name>.integration`.
- CLI verb shapes: `vibe <integration> <action>`, the reserved core verbs
  (`status`, `version`, `doctor`), and `--json` on read verbs.
- Config-key conventions: `.vibe/config.toml` shared keys, `.vibe/<integration>.toml`
  per-integration files, presence = enablement, secret-reference scheme
  (`gh:`/`env:`/`op:`), precedence (explicit > env > file).
- Artifact format: the layered `.vibe/` directory described in §3.

**Internal / may change without a major bump:**

- Anything under `vibe.integrations.<name>.*` except `integration`.
- `vibe._internal.*`, any `_`-prefixed name, and CLI dispatch internals.
- The concrete config object library (dataclass vs. pydantic) — only the *shape*
  (frozen, typed, explicit fields) is promised.

---

## 8. Worked check — the PR-automation integration, expressed against this contract

To satisfy the acceptance criterion "the PR automation integration is fully
expressible against the contract without referencing app/repo-local code," here is
the full surface of `vibe[pr-autopilot]` stated only in this contract's terms:

- **Install:** `uv pip install 'vibe[pr-autopilot]'`.
- **Import:** `from vibe.integrations.pr_autopilot import integration, PRAutopilotConfig`.
- **Config (injected):** `PRAutopilotConfig(github_owner=..., linear_team=...,
  anthropic_api_key=...)` — or loaded from `.vibe/pr-autopilot.toml` (presence =
  enabled) with `anthropic_api_key = "gh:ANTHROPIC_API_KEY"`.
- **CLI:** `vibe pr-autopilot configure`, `status`, `inspect`, `enable`,
  `disable`, and engine-gated `run`; status is also surfaced under `vibe status`.
- **Missing extra:** bare `vibe pr-autopilot run` →
  `MissingExtraError: install 'vibe[pr-autopilot]'`.
- **No LIFT/DEAL import** anywhere in the surface above. The engine (VIBE-128) lands
  *behind* this seam; nothing here references app/repo-local code.

This is the contract VIBE-128/129 build against, VIBE-86 implements the seam for,
and VIBE-85 packages.

The live skeleton is documented in
[`docs/packaging/integration-skeleton.md`](integration-skeleton.md).

---

## 9. Out of scope (deferred, with forward-compat note)

- **Implementing the PR-automation engine** — M2 / VIBE-128.
- **The four-module taxonomy** — future; full treatment in VIBE-88. Forward-compat
  note only: the `vibe.integrations.<name>` namespace and the `Integration`
  registration object are designed so a future "module" is just an integration with
  a richer surface — no namespace reshuffle required to add the four-module set.
- **Distribution vendor + update contract** — VIBE-87 (`docs/packaging/distribution.md`).
- **uv packaging mechanics, build backend, lockfile, release workflow** — VIBE-85.

---

## Downstream readiness checklist

A ticket can be implemented from this doc when it can answer "yes" to its row:

- **VIBE-85** — every import path, CLI verb, config key, and the extra-naming rule
  it must package are named here? ✅ (§1, §5, §6)
- **VIBE-86** — the registration seam, module layout, extra wiring, and the
  decoupling guardrail's target are specified? ✅ (§2, §4, §6)
- **VIBE-179** — the artifact format, secret-reference boundary, and `vibe status`
  contract the DX prototype writes against are fixed? ✅ (§3, §5.3, §5.5)
- **VIBE-128/129 (M2)** — the PR-automation surface is expressible with no app-code
  reference? ✅ (§8)
