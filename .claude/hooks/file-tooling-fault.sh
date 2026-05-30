#!/usr/bin/env bash
# Auto-file VIBE tooling faults (VIBE-206).
#
# PostToolUse(Bash) hook. When a VIBE CLI crashes it emits a VIBE_TOOLING_FAULT
# marker (see lib/vibe/cli/errors.py). This hook detects that marker in the tool
# output and files (or de-dups onto) an Urgent DX ticket via
# `bin/ticket file-tooling-issue`. It no-ops for every other Bash call.
#
# Kill switch: set VIBE_NO_AUTOFILE=1 to disable filing.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [ "${VIBE_NO_AUTOFILE:-0}" = "1" ]; then
  exit 0
fi

# Hook payload (JSON) arrives on stdin; the python helper parses it and shells
# out to bin/ticket only when the marker is present.
exec python3 "$REPO_ROOT/.claude/hooks/file-tooling-fault.py" "$REPO_ROOT"
