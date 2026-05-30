"""Shared CLI fault signalling for VIBE tooling.

When a ``bin/*`` CLI crashes with an *unexpected* exception (not a user/usage
error), it self-classifies as a **tooling fault** and emits a machine-readable
marker on stderr. The Claude Code ``PostToolUse`` hook keys on this marker to
auto-file an Urgent DX ticket via ``bin/ticket file-tooling-issue`` — executing
the ``agent_instructions/CLI.md`` "CLI's-fault" doctrine without the agent
having to remember to do it by hand.

The CLI is the only party that reliably knows whether *it* crashed (an
unexpected exception) versus the caller making a normal usage error (handled by
click as ``UsageError``/``Abort``). Keying the hook on a marker the CLI emits
about itself is what keeps auto-filing low-noise.
"""

from __future__ import annotations

import json
import re
import sys
import traceback
from collections.abc import Callable

import click

# Distinct exit code so wrappers/hooks can tell a self-classified tooling fault
# apart from ordinary failures (1) and click usage errors (2).
TOOLING_FAULT_EXIT_CODE = 97

# Stderr marker the PostToolUse hook greps for. Followed by a JSON payload.
FAULT_MARKER = "VIBE_TOOLING_FAULT:"

_HEX = re.compile(r"0x[0-9a-f]+")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_PATH = re.compile(r"(?:/[^\s:'\"]+)+")
_LINE = re.compile(r"line \d+")
_NUM = re.compile(r"\d+")
_WS = re.compile(r"\s+")


def normalize_signature(text: str) -> str:
    """Reduce an error string to a stable fingerprint for deduplication.

    Strips volatile detail (hex addresses, UUIDs, absolute-ish paths, line
    numbers, and any remaining digits) and lowercases/collapses whitespace, so
    the *same* fault re-files onto one ticket instead of spawning duplicates
    when incidental detail (a line number, a temp path) shifts between runs.
    """
    s = text.strip().lower()
    s = _HEX.sub("<hex>", s)
    s = _UUID.sub("<uuid>", s)
    s = _PATH.sub("<path>", s)
    s = _LINE.sub("line <n>", s)
    s = _NUM.sub("<n>", s)
    s = _WS.sub(" ", s)
    return s.strip()


def _argv_command() -> str:
    """Best-effort subcommand name from argv, for the fault payload."""
    positional = [a for a in sys.argv[1:] if not a.startswith("-")]
    return positional[0] if positional else ""


def emit_fault_marker(module: str, command: str, exc: BaseException) -> None:
    """Print the machine-readable fault marker (+ JSON payload) to stderr."""
    payload = {
        "module": module,
        "command": command,
        "type": type(exc).__name__,
        "message": str(exc),
        "signature": normalize_signature(f"{type(exc).__name__}: {exc}"),
    }
    click.echo(f"{FAULT_MARKER} {json.dumps(payload)}", err=True)


def run_cli(group: Callable[..., object], module: str) -> None:
    """Run a click entrypoint, self-classifying unexpected crashes as faults.

    click handles its own ``UsageError``/``Abort`` and turns them (plus normal
    completion) into ``SystemExit`` — those are user/usage outcomes and pass
    through untouched. Any *other* exception escaping the group is an
    unexpected crash: print the traceback (for the human/agent reading the
    output), emit the fault marker, and exit with ``TOOLING_FAULT_EXIT_CODE``.
    """
    try:
        group(standalone_mode=True)
    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 - top-level tooling-fault safety net
        traceback.print_exc()
        emit_fault_marker(module, _argv_command(), exc)
        sys.exit(TOOLING_FAULT_EXIT_CODE)
