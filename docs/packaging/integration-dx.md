# Claude Code Integration DX Prototype

> Status: VIBE-179 prototype contract. This sets the reusable feel for
> configuring integrations from Claude Code; the production command surface and
> PR automation engine remain owned by the M2 tickets.

## Thesis

In Claude Code, the agent is the operator and the human is the approver and
value-provider. Elegant integration DX therefore means making Claude able to
drive the provider tools directly, with small, well-timed human handoffs for
things only the human can provide.

Vibe owns the seams:

- the reviewable `.vibe/` desired-state artifact;
- provider-secret references rather than committed secret values;
- status and drift reconciliation across tools;
- crisp human handoffs when a provider needs a value, login, billing action, or
  subjective choice.

Vibe does not re-skin providers. Claude should still show `gh`, `flyctl`,
`vercel`, `neonctl`, or provider MCP/API calls in the transcript.

## Reusable command shape

Each integration should expose the same prototype verbs through the VIBE-84
registry when possible:

```bash
bin/vibe <integration> configure
bin/vibe <integration> status
bin/vibe <integration> inspect
bin/vibe <integration> enable
bin/vibe <integration> disable
```

The root status command summarizes every configured integration:

```bash
bin/vibe status
```

Claude Code slash commands under `.claude/commands/` must stay thin. They may
sequence CLI calls and describe the narration contract, but state changes and
status reconciliation live in Python.

## Layered artifact contract

Configuration is layered and reviewable:

```text
.vibe/config.toml             # shared identity and wiring
.vibe/<integration>.toml      # one file per enabled integration
```

The per-integration file's presence is the enablement bit. Disable flows remove
that active `.toml` from the set, optionally preserving a `.disabled` copy for
easy re-enable. This keeps "what is enabled?" visible with a simple listing.

Secret values are never written to committed files. Store references:

```toml
[secrets]
anthropic_api_key = "gh:ANTHROPIC_API_KEY"
```

Claude verifies or scaffolds the referenced secret with the provider's native
tool, then reruns status. For PR automation, the prototype shows:

```bash
gh secret list --json name
gh secret set ANTHROPIC_API_KEY
```

## Configure flow

The configure verb should be safe to rerun:

1. Infer local state first: repo identity, existing `.vibe/` files, provider CLI
   availability, current auth, and existing secrets/configuration.
2. Confirm by reporting what was inferred; ask only for missing values that
   cannot be inferred safely.
3. Write `.vibe/config.toml` and `.vibe/<integration>.toml` deterministically.
4. Show the native provider commands that were run or that need the human's
   secret/account value.
5. End with the exact status command to run next.

Rerunning configure should produce either no diff or a deterministic update to
the same keys. It must not duplicate sections, append repeated blocks, or replace
provider-owned state without saying so.

## Status and drift output

Status output should answer the same questions for every integration:

- configured: is the desired-state artifact present?
- enabled: is the active per-integration `.toml` present?
- authed: can the native provider tool authenticate?
- secret/config refs: do referenced provider-side values exist?
- health: is the integration usable, disabled, or waiting on a handoff?
- drift: what desired state is missing or unverifiable?
- next: the smallest useful command or human action.

Use direct text labels (`ok`, `missing`, `unknown`, `needs human secret handoff`)
so the output is readable in a terminal transcript and easy for agents to parse.

## PR automation prototype

VIBE-179 wires PR automation first:

```bash
bin/vibe pr-autopilot configure
bin/vibe pr-autopilot status
bin/vibe pr-autopilot inspect
bin/vibe pr-autopilot enable
bin/vibe pr-autopilot disable
```

The engine verb remains gated by the future optional extra:

```bash
bin/vibe pr-autopilot run
```

That split lets Claude prove the configuration experience now while M2 owns the
production PR automation runner.
