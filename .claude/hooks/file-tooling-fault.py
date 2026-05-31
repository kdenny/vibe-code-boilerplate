#!/usr/bin/env python3
"""PostToolUse hook helper: auto-file VIBE tooling faults (VIBE-206).

Reads the Claude Code hook payload (JSON) on stdin. If a VIBE CLI emitted the
``VIBE_TOOLING_FAULT`` marker in the tool output, parse its JSON payload and
shell out to ``bin/ticket file-tooling-issue`` (which de-dups + labels + sets
Urgent priority). Stays silent and exits 0 for everything else, so it is safe
to attach to *all* Bash invocations — it only acts on the explicit marker.
"""

import json
import subprocess
import sys

MARKER = "VIBE_TOOLING_FAULT:"


def _flatten_text(obj: object) -> str:
    """Concatenate all string values reachable in a nested JSON structure."""
    if obj is None:
        return ""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return " ".join(_flatten_text(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(_flatten_text(v) for v in obj)
    return str(obj)


def main() -> int:
    repo_root = sys.argv[1] if len(sys.argv) > 1 else "."
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    text = _flatten_text(data.get("tool_response"))
    idx = text.find(MARKER)
    if idx == -1:
        return 0

    rest = text[idx + len(MARKER) :].lstrip()
    brace = rest.find("{")
    if brace == -1:
        return 0
    try:
        # raw_decode tolerates trailing output after the JSON payload.
        payload, _ = json.JSONDecoder().raw_decode(rest[brace:])
    except (json.JSONDecodeError, ValueError):
        return 0

    cli = payload.get("module") or "unknown"
    command = payload.get("command") or ""
    etype = payload.get("type") or "Error"
    message = payload.get("message") or ""
    signature = payload.get("signature") or ""

    summary = f"{etype} in {cli} {command}".strip()[:200]
    detail = f"{etype}: {message}"

    subprocess.run(  # noqa: S603 - fixed argv, values from our own CLI marker
        [
            f"{repo_root}/bin/ticket",
            "file-tooling-issue",
            "--cli",
            cli,
            "--summary",
            summary,
            "--detail",
            detail,
            "--signature",
            signature,
        ],
        check=False,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
