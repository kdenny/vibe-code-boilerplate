# Packaged Vibe — uv Build & Release Workflow (VIBE-85)

This is the repeatable procedure for taking a clean checkout to a publishable
private `vibe` artifact. The v0 publish target is the private git tag chosen in
[`distribution.md`](distribution.md): no package index upload is configured.

## Package contract

| Concern | Value |
|---|---|
| Distribution name | `vibe` |
| Import package | `vibe` |
| Build backend | `setuptools.build_meta` |
| Runtime Python | `>=3.11` |
| Version source | `VERSION` |
| Release tag | `vMAJOR.MINOR.PATCH` matching `VERSION` |
| Lockfiles | `uv.lock` (default), `requirements.lock` (pip fallback) |

Bare `vibe` installs the core runtime dependencies only. Integration/provider
dependencies are optional extras named for the integration slug, e.g.
`vibe[pr-autopilot]`. Dev tools live in the uv `dev` dependency group.

## Fresh-checkout install

```bash
command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"

UV_PROJECT_ENVIRONMENT=.venv uv sync --frozen --group dev --extra pr-autopilot
export PATH="$PWD/.venv/bin:$PATH"
```

For a non-uv environment, use the fallback lock:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.lock
pip install -e . --no-deps
```

## Updating dependencies

After changing `[project.dependencies]`, `[project.optional-dependencies]`, or
`[dependency-groups]` in `pyproject.toml`, regenerate both locks in the same PR:

```bash
uv lock
uv pip compile pyproject.toml --group dev --all-extras --generate-hashes -o requirements.lock
```

`uv.lock` is the source for reproducible uv installs. `requirements.lock` mirrors
the same closure for pip-only fallback environments and cache compatibility.

## Local build and test gate

```bash
unset LINEAR_API_KEY
bin/ci-local --fast
uv build
uv run python -c "import importlib.metadata as m; assert m.version('vibe') == open('VERSION').read().strip()"
```

`uv build` must produce both:

- `dist/vibe-<version>-py3-none-any.whl`
- `dist/vibe-<version>.tar.gz`

## Version bump convention

VIBE uses SemVer for the package version in `VERSION`:

- PATCH: fixes and internal changes that do not alter the promised VIBE-84
  package surface.
- MINOR: additive, backwards-compatible changes to the promised surface.
- MAJOR: breaking changes to the promised surface.

Use the `Version Bump` workflow to write `VERSION`, or run the equivalent local
CLI command and open a normal PR:

```bash
vibe bump patch  # or minor / major
```

Before a release, add a matching `## <version>` section to `CHANGELOG.md`.

## Release workflow

The GitHub Actions `Release` workflow is the release gate. It:

1. Syncs from `uv.lock` with the `dev` group and `pr-autopilot` extra.
2. Verifies the requested version, `VERSION`, and `v<version>` tag agree.
3. Requires a matching `CHANGELOG.md` section.
4. Runs `bin/ci-local --fast`.
5. Runs `uv build` and checks wheel metadata (`Name: vibe`, matching version).
6. Uploads the wheel and sdist as workflow artifacts.
7. Dry-runs publish by default; when `dry_run=false`, creates and pushes the
   annotated git tag. The tag is the v0 publish artifact.

### Dry-run 0.1.0

From `main` at the release commit:

1. Confirm `VERSION` is `0.1.0`.
2. Confirm `CHANGELOG.md` contains `## 0.1.0`.
3. Run the `Release` workflow with:
   - `version = 0.1.0`
   - `dry_run = true`
4. Inspect the uploaded `vibe-0.1.0-dist` artifact.

### Publish 0.1.0

After the dry-run is green, rerun the workflow with:

- `version = 0.1.0`
- `dry_run = false`

The workflow creates and pushes annotated tag `v0.1.0`. Do not delete or move a
published tag; supersede a bad release with a new SemVer tag.

## Consumer install

Downstream repos should pin the private git tag in `pyproject.toml` and commit
their own `uv.lock`:

```toml
[project]
dependencies = ["vibe[pr-autopilot]"]

[tool.uv.sources]
vibe = { git = "https://github.com/kevin-earl-denny/vibe-code-boilerplate", tag = "v0.1.0" }
```

Then run:

```bash
uv sync
```

Rollback is symmetric: restore the prior tag in `[tool.uv.sources]`, run
`uv lock --upgrade-package vibe && uv sync`, and commit the lockfile diff.
