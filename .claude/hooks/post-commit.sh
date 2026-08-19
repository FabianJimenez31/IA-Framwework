#!/bin/bash
# Records the decision state after every commit.
#
# The commit is the moment a choice becomes fact: the message says what and why,
# the diff says where, and the sha makes it addressable. That is a complete
# decision record already — it just needs to be persisted somewhere searchable.
#
# A post-commit hook must never fail the commit it follows.

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
CAPTURE="$ROOT/scripts/memory/capture_stage.sh"
[ -x "$CAPTURE" ] || exit 0

# Skip when the harness is under an emergency bypass; the gate records that
# separately and an incident commit should not be slowed down.
if [ -f "$ROOT/.claude/hooks/emergency_state.sh" ]; then
    # shellcheck source=/dev/null
    source "$ROOT/.claude/hooks/emergency_state.sh"
    if harness_emergency_active; then
        exit 0
    fi
fi

bash "$CAPTURE" decision >/dev/null 2>&1 || true
exit 0
