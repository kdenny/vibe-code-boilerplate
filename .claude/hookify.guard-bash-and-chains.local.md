---
name: guard-bash-and-chains
enabled: true
event: bash
action: warn
pattern: ^(?!.*\|\|).*(?:2>\s*/dev/null\s*&&|&&[^&]*\b(?:grep|egrep|fgrep|rg)\b|\b(?:grep|egrep|fgrep|rg)\b[^&]*&&)
---

⚠️ **Fragile `&&` chain — this is the pattern that keeps cascading.**

`grep` exits **1 when it finds nothing** (not an error — just "no match"), and
`cmd 2>/dev/null &&` continues even when the first command failed silently. Inside
an `&&` chain that non-zero exit **aborts the rest of the chain**, and because
Claude Code runs sibling Bash calls as a **parallel batch**, one aborted command
**cancels every other call in the turn** ("Cancelled: parallel tool call … errored").

Fix one of these ways:
- **Separate output from gating.** If `grep` is *filtering for display*, end the
  command there or use `;` instead of `&&`: `cmd1; cmd1b | grep foo; cmd2`.
- **Add an `||` fallback** so failure is handled (this also silences this warning):
  `cd /tmp/x 2>/dev/null && do_thing || echo "dir missing"`.
- **Append `|| true`** to a step whose non-zero exit is expected/harmless.
- **Don't batch fragile exploratory commands** as parallel siblings — if one may
  legitimately exit non-zero, run it as its own call so a sibling can't cancel it.

If this command really is an intentional gate (`grep -q … && act`), run it
standalone, not in a parallel batch, so a no-match can't take siblings down.
