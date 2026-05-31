---
description: Configure and inspect Vibe integrations through the CLI-driven Claude Code DX
---

# /vibe - integration operator surface

Use this when a human asks Claude Code to configure, inspect, enable, or disable
a Vibe integration. The command is an operator guide only: the `vibe` CLI owns the
state changes and status reconciliation.

## PR automation prototype

Configure or refresh the prototype artifacts:

```bash
bin/vibe pr-autopilot configure
```

Then show the reconciled state:

```bash
bin/vibe status
bin/vibe pr-autopilot inspect
```

If the CLI reports that the Anthropic key is missing, ask the human for the value
and run the native provider command it prints:

```bash
gh secret set ANTHROPIC_API_KEY
bin/vibe pr-autopilot status
```

Enable or disable the integration with the CLI, then confirm with status:

```bash
bin/vibe pr-autopilot enable
bin/vibe pr-autopilot disable
bin/vibe status
```

## Claude narration contract

- Say what you inferred before asking the human anything.
- Show the native provider command in the transcript (`gh repo view`,
  `gh secret list`, `gh secret set`) instead of implying Vibe owns GitHub.
- Ask only for values Claude cannot infer or fetch safely, especially secret
  values and account/billing decisions.
- Treat `.vibe/config.toml` plus `.vibe/<integration>.toml` as the reviewable
  artifact. Secret files contain provider references such as
  `gh:ANTHROPIC_API_KEY`, never the secret value.
