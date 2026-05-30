# Packaged Vibe — Private Distribution & Downstream Update Contract (v0)

> **Status: v0 decision doc (VIBE-87).** This makes the call the VIBE-83 wall
> intentionally left open: **how downstream repos and collaborators consume private
> `vibe` releases for v1.** Grounded in the VIBE-83 contract and the VIBE-84 package
> surface (`docs/packaging/package-contract.md`). It feeds the VIBE-85 release
> workflow and is exercised by the VIBE-89 gate.
>
> **Decision (v0): git tag + `uv`.** Private distribution is a git ref pinned by
> tag, installed with `uv`. No package index, no wheel-hosting infra. Rationale and
> the full option scoring below.

---

## 1. The decision in one line

```
vibe @ git+https://github.com/kevin-earl-denny/vibe-code-boilerplate@v0.1.0
```

Downstream repos depend on `vibe` as a **git dependency pinned to an annotated tag**,
resolved and locked by `uv`. Auth reuses credentials the consumer already has (the
PR-autopilot GitHub App token in CI; a developer's existing GitHub auth locally;
SSH/deploy key for friend repos). There is **no new index, no new account, and no
new secret** beyond what is already needed to clone a private repo.

---

## 2. Options evaluated

| Option | What it is |
|---|---|
| **(a) git tag + uv** ✅ **chosen** | Depend on `vibe @ git+https://…@vX.Y.Z`; a tag *is* the release. `uv` resolves + locks the exact commit. |
| (b) GitHub Releases wheel | CI builds a wheel, attaches it to a GitHub Release; consumers install the wheel asset URL (auth'd download). |
| (c) Private index | Push wheels to Cloudsmith / Gemfury / AWS CodeArtifact; consumers configure an extra index URL + token. |

### Scoring against the fixed criteria

Legend: ✅ strong · 🟡 workable · ❌ weak.

| Criterion | (a) git tag + uv | (b) Releases wheel | (c) Private index |
|---|---|---|---|
| **CI install** (GitHub-hosted job, PR-autopilot App token / deploy key) | ✅ token already grants repo read; `git+https` with the token "just works" | 🟡 must resolve the Release asset URL + auth the download (API call or `gh release download`) | 🟡 works, but needs an *extra* index URL + a *separate* registry token in CI secrets |
| **Runner image** (bakeable into self-hosted `fly-ephemeral`) | ✅ `uv sync` from a committed lock bakes cleanly; only git creds needed at build | ✅ wheel is a static artifact, trivially bakeable | 🟡 bakeable, but the image now depends on a third-party registry being up at build time |
| **Friend-managed repos** (collaborators, no org seats) | ✅ a repo collaborator / deploy key already has the access; SSH form (`git+ssh`) needs nothing new | 🟡 collaborator can download assets, but the install string is uglier and asset auth is fiddlier | ❌ each friend needs a registry account/token — exactly the per-seat friction we're avoiding |
| **Pinning vs. floating + upgrade/rollback** | ✅ tag pins; `uv.lock` pins the commit hash; rollback = change the tag, re-lock | ✅ version in the asset pins; rollback = install the prior wheel | ✅ standard semver pinning; rollback = pin prior version |
| **New infra / cost / secret burden** | ✅ **none** — git is the registry | 🟡 minor: a CI release step + asset-auth logic; still GitHub-only | ❌ new vendor, new bill, new token rotation, new failure mode |

**Net:** (a) wins on the three criteria that matter most for this operator (CI
auth, friend repos, zero new burden) and ties on pinning/rollback. (b) is the
closest runner-up and the natural upgrade path *if* we later need a built artifact
(e.g. faster cold installs on the runner) without leaving GitHub. (c) only earns its
keep at a scale we are explicitly not at (many external consumers, true semver
channels, org-managed seats).

---

## 3. Why git tag + uv (rationale against the decision flip-points)

- **The auth we already have is the package auth.** Every consumer of a private
  `vibe` already needs to read the private repo. `git+https`/`git+ssh` reuses that
  credential; no second credential system to provision, rotate, or document. This is
  the single biggest reason — it collapses the "secret-management burden" criterion
  to zero.
- **Matches the agent-as-operator model.** `uv` is already the default tooling
  (VIBE-85). `uv add 'vibe @ git+…@vX.Y.Z'` + a committed `uv.lock` is one command
  Claude can run and verify, with a hash-pinned, reproducible result.
- **Solo team / small blast radius.** No registry uptime to babysit, no per-seat
  onboarding for friends. The simplest thing that satisfies every criterion.
- **Reversible.** If cold-install time on the `fly-ephemeral` runner becomes a real
  bottleneck, **(b) GitHub Releases wheel is a strict, GitHub-only upgrade** —
  same auth domain, just a prebuilt artifact. We can adopt it for the runner image
  *without* changing the consumer contract for friend repos. This decision does not
  trap us.

**Flip-points (when to revisit):** (1) external consumers who are *not* repo
collaborators appear → reconsider (c); (2) git-clone install time dominates runner
cold-start (VIBE-185 territory) → adopt (b) for the runner image; (3) we need true
floating semver channels (`~=0.1`) across many repos → reconsider (c).

---

## 4. Consumer install snippet (chosen path)

### 4.1 `pyproject.toml` (the durable, locked form — preferred)

```toml
[project]
dependencies = [
    "vibe",
]

[tool.uv.sources]
vibe = { git = "https://github.com/kevin-earl-denny/vibe-code-boilerplate", tag = "v0.1.0" }
```

Then:

```bash
uv sync          # resolves + writes the exact commit into uv.lock; reproducible
```

With an integration extra (per VIBE-84 §6):

```toml
dependencies = ["vibe[pr-autopilot]"]
```

### 4.2 Ad-hoc / one-off install

```bash
uv pip install 'vibe @ git+https://github.com/kevin-earl-denny/vibe-code-boilerplate@v0.1.0'
```

### 4.3 Auth per consumer

| Consumer | Mechanism |
|---|---|
| **CI (GitHub-hosted)** | PR-autopilot **GitHub App token** (or `GITHUB_TOKEN`) injected as the git credential: `git config --global url."https://x-access-token:${TOKEN}@github.com/".insteadOf "https://github.com/"` before `uv sync`. |
| **Self-hosted `fly-ephemeral` runner** | Same token baked/injected at build; `uv sync` from the committed lock. (Future: swap to a prebuilt wheel per §3 flip-point 2.) |
| **Friend-managed repo** | Repo-collaborator access; use the **SSH form** `git+ssh://git@github.com/…` so the developer's existing key authorizes the clone — no token to share. |
| **Local dev (maintainer)** | Existing `gh auth` / credential helper; nothing extra. |

> **No secret values in committed files.** The token is supplied via the
> environment / git credential helper, never written into `pyproject.toml`,
> `uv.lock`, or a `.vibe/` file (consistent with VIBE-84 §3.2's secret-reference
> rule).

---

## 5. Downstream update contract

### 5.1 Pinning policy

- Downstream repos **pin to an annotated tag** (`tag = "v0.1.0"`), never to a branch
  or floating ref. `uv.lock` additionally pins the resolved **commit hash** — the
  tag is the human handle, the lock is the reproducibility guarantee.
- v0 uses **explicit pins only** (no `~=`/floating ranges). Floating channels are a
  flip-point (§3), not a v0 feature.

### 5.2 Versioning & release handle

- Tags are `vMAJOR.MINOR.PATCH`, annotated, created by the VIBE-85 release workflow
  from `VERSION`. The tag is the sole release artifact for v0.
- Semver intent: PATCH = fixes/no surface change; MINOR = additive, stability-promise
  preserving (VIBE-84 §7); MAJOR = a break to a promised surface.

### 5.3 Upgrade cadence

- Downstream repos upgrade **deliberately**, by bumping the tag in
  `[tool.uv.sources]` and running `uv lock --upgrade-package vibe && uv sync`.
- Recommended cadence: adopt PATCH/MINOR within one cycle of release; MAJOR upgrades
  are scheduled work (read the changelog, expect surface changes).
- **No silent auto-upgrade.** Because pins are explicit, a downstream repo never
  moves versions without a committed diff to `pyproject.toml` + `uv.lock` — the
  upgrade is always reviewable.

### 5.4 Rollback expectation

- Rollback is **symmetric with upgrade**: set the tag back to the prior `vX.Y.Z`,
  `uv sync`, commit. Because the previous lock entry pinned a commit hash, the prior
  state is byte-reproducible.
- The release workflow (VIBE-85) **must not delete or move published tags** — tags
  are immutable so a rollback target always exists. A bad release is superseded by a
  new tag, never by rewriting an old one.

### 5.5 Staying in sync without copy-paste drift

- Downstream repos consume `vibe` **only** as this git dependency — never by copying
  `vibe` source into the repo. The dependency edge *is* the sync mechanism; there is
  no vendored copy to drift.
- The owned `.vibe/` artifact (VIBE-84 §3) lives in the downstream repo and is
  version-independent config; upgrading `vibe` does not require regenerating it
  (config keys are part of the stability promise). `vibe status` (VIBE-84 §5.3)
  surfaces any drift between the installed version's expectations and the artifact.
- A CHANGELOG (maintained by VIBE-85's release workflow) is the single place
  downstream readers learn what a tag changed — no need to diff source across repos.

---

## 6. Wiring back into VIBE-85's release workflow

This decision finalizes the publish step VIBE-85 left pluggable. The concrete
contract VIBE-85 implements:

1. **Build + test gate** (VIBE-85): `uv build` produces wheel + sdist; tests must
   pass before any tag is published. *(The wheel/sdist are still built for
   verification and as the seed for the §3 flip-point — git-tag distribution does
   not require publishing them anywhere for v0.)*
2. **Tag = publish.** On a green release, the workflow creates an **annotated,
   immutable** tag `vX.Y.Z` from `VERSION` and pushes it. That tag is the published
   artifact.
3. **No index push, no asset upload** for v0. The publish step is "create + push
   tag," not "upload wheel." (If flip-point 2 is hit, VIBE-85 adds an *additional*
   `gh release upload` of the already-built wheel — additive, non-breaking.)
4. **Changelog stamp.** The workflow records the tag's changes in `CHANGELOG.md` so
   §5.5's sync contract has a source.

VIBE-89's gate exercises the acceptance criterion below against this wiring.

---

## 7. Acceptance criteria (mapped)

- **One option selected with documented rationale against every criterion** — §2
  table scores all three on all five criteria; §3 gives the rationale and
  flip-points. ✅
- **A real downstream-style install of `vibe` from the chosen path succeeds in a
  fresh environment** — install snippets + per-consumer auth in §4; **proof
  exercised by the VIBE-89 gate** (a clean-env `uv sync` of a `git+https`-pinned
  `vibe`). ✅ (definition here; execution is VIBE-89's gate)
- **The update/pinning/rollback contract is written and unambiguous** — §5. ✅

---

## 8. Out of scope

- **Public PyPI distribution** — private only for v0.
- **Standalone binary path** — later milestone.
- **uv packaging mechanics, build backend, lockfile creation, the release workflow
  implementation** — VIBE-85 (this doc only fixes the *publish target* it plugs in).
- **The package surface / import paths / extras naming** — VIBE-84
  (`docs/packaging/package-contract.md`).
