# Agent-Authored PR: Expected Shape (Revamp Period)

This is the template + a worked example for PRs opened by coding agents during the
VIBE revamp. It mirrors the contract in [`CLAUDE.md`](../../CLAUDE.md) and the gates
in [`.coderabbit.yaml`](../../.coderabbit.yaml). Copy the template, fill every
section. CodeRabbit's `pre_merge_checks` will request changes if the title or the
required sections are missing.

---

## Template

**Title:** `VIBE-<number>: <imperative summary>`

```markdown
## What changed and why
- <bullet 1>
- <bullet 2>
- <bullet 3>   (3–5 bullets max)

## Staged migration step
- This PR is step <X> of <the seam being extracted>.
- Intentionally deferred to a later PR: <what and why>.
- Big-bang avoided because: <how this stays incremental>.

## Test proof (local, live)
Commands run and results:

    bin/ci-local                 ✅
    <module test command>        ✅

CLI smoke-test matrix (only for CLI changes — every subcommand of the modified CLI):

| Subcommand            | Result | Notes                    |
|-----------------------|--------|--------------------------|
| `bin/<cli> <cmd-a>`   | ✅     |                          |
| `bin/<cli> <cmd-b>`   | ✅     |                          |
| `bin/<cli> <cmd-c>`   | ⏸️     | deferred → VIBE-<n>      |

## Module isolation
- Modules touched still run and test in isolation: <how verified>.
- No new hidden coupling / global state introduced.

## Sync confirmation
- [ ] Structure / run-validation flow / agent-contract changed → `.coderabbit.yaml`
      and `CLAUDE.md` updated in this PR.
- [ ] OR: none of the above were affected (no config change needed).

## Speed
- Speed observations / ideas surfaced (or "none"): <...>

## Labels
- Type: <Bug|Feature|Chore|Refactor> · Risk: <Low|Medium|High> · Area: <...>
```

---

## Worked example

**Title:** `VIBE-142: Extract ticket-tracker client into lib/vibe/trackers`

```markdown
## What changed and why
- Moved the Linear client out of `lib/vibe/cli/ticket.py` into a new
  `lib/vibe/trackers/linear.py` behind a `TrackerClient` protocol.
- `bin/ticket` now depends on the protocol, not the concrete Linear module.
- No behavior change: every `bin/ticket` subcommand produces identical output.

## Staged migration step
- Step 1 of 3 in extracting the tracker seam. This PR only moves the Linear
  client and introduces the protocol.
- Deferred: a Shortcut implementation (VIBE-143) and removing the legacy import
  shim (VIBE-144).
- Big-bang avoided: the old import path still works via a one-line re-export, so
  nothing downstream breaks in this PR.

## Test proof (local, live)
    bin/ci-local                         ✅
    python -m pytest tests/test_cli_ticket.py   ✅ (18 passed)

CLI smoke-test matrix:

| Subcommand                              | Result | Notes |
|-----------------------------------------|--------|-------|
| `bin/ticket list`                       | ✅     |       |
| `bin/ticket get VIBE-138`               | ✅     |       |
| `bin/ticket create "Test"`              | ✅     | cleaned up after |
| `bin/ticket update VIBE-138 --status …` | ✅     |       |

## Module isolation
- `lib/vibe/trackers/linear.py` imports and runs without the CLI layer
  (verified via `python -c "from lib.vibe.trackers.linear import LinearClient"`).
- No new global state; the client is instantiated and injected.

## Sync confirmation
- [x] Structure changed (new module seam) → no change to local run/validation
      flow or the agent-PR contract, so `.coderabbit.yaml`/`CLAUDE.md` unchanged.
      (Logged here per the sync rule.)
- [ ] OR: none of the above were affected.

## Speed
- Observation: `bin/ci-local` spends ~4s re-importing the tracker on every run.
  Filed VIBE-145 to lazy-load tracker modules.

## Labels
- Type: Refactor · Risk: Medium · Area: Backend
```

---

## What makes this pass vs. fail review

**Passes** because it: references the ticket in the title; is a clearly *staged*,
behavior-preserving extraction; ships live test proof with a full CLI matrix;
confirms isolation and the sync rule; and proactively surfaces a speed idea as a
follow-up ticket.

**Would fail** if it: omitted the smoke-test matrix; changed behavior without
tests; collapsed all three steps into one big-bang PR; increased coupling; or
changed the run/validation flow without updating `.coderabbit.yaml` and `CLAUDE.md`.
