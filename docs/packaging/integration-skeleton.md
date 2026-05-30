# Packaged Vibe Integration Skeleton

> **Status:** VIBE-86 reference shape. Today the implementation lives under
> `lib.vibe.integrations.*`; VIBE-182 re-homes the package to the target
> `vibe.integrations.*` namespace without changing the seam below.

## Module layout

```text
lib/vibe/integrations/<integration>/
  __init__.py        # exports exactly: integration, <Integration>Config
```

`__init__.py` is the public surface. Everything below it is internal unless a
future contract explicitly says otherwise.

## Required exports

```python
from dataclasses import dataclass

from lib.vibe.cli import Integration, verb


@dataclass(frozen=True)
class ExampleConfig:
    github_owner: str


integration = Integration(
    name="example",
    config_cls=ExampleConfig,
    verbs=(verb("status", handler=status_handler, help="Show example status"),),
    extra="example",
    extra_module="vibe_example",
    check=status_handler,
    entrypoints={"status": status_handler},
)

__all__ = ["ExampleConfig", "integration"]
```

- `config_cls` is the typed config schema consumed by core and downstream callers.
- `verbs` declares the `vibe <integration> <verb>` CLI surface.
- `entrypoints` names callable engine hooks for embedded use.
- `extra` names the install extra shown to users.
- `extra_module` is the importable module that proves the extra's runtime
  dependency is installed. If it is missing, core raises `MissingExtraError` with
  an actionable `uv pip install 'vibe[<integration>]'` message.

## Decoupling guardrail

Integration modules must not import downstream app code (`app`, `src`, `lift`,
`deal`, etc.) or assume a repo-local layout. `tests/test_integrations_guardrails.py`
parses integration imports and fails if a deliberate app-code import is added.

## Reference consumer

`lib.vibe.integrations.pr_autopilot` is the reference skeleton for VIBE-128. It
exports `PRAutopilotConfig` and `integration`, declares `run` / `status` verbs,
and is gated by the `pr-autopilot` extra until the real engine package lands.
