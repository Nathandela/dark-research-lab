#!/bin/bash
# decision-reminder.sh - Advisory reminder to log methodological decisions
# Fires on UserPromptSubmit when cook-it is active

REPO_ROOT="${DRL_REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
PHASE_STATE="$REPO_ROOT/.claude/.ca-phase-state.json"
LAST_PHASE_FILE="$REPO_ROOT/.claude/.drl-last-phase"

# Exit silently if no phase state (not in cook-it)
[ -f "$PHASE_STATE" ] || exit 0

# Read current phase
CURRENT_PHASE=$(python3 -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        state = json.load(f)
    if state.get('cookit_active'):
        print(state.get('current_phase', ''))
except Exception:
    pass
" "$PHASE_STATE" 2>/dev/null)

# Exit if not in active cook-it
[ -z "$CURRENT_PHASE" ] && exit 0

# Read last known phase
LAST_PHASE=""
[ -f "$LAST_PHASE_FILE" ] && LAST_PHASE=$(cat "$LAST_PHASE_FILE")

# If phase changed, emit reminder
if [ "$CURRENT_PHASE" != "$LAST_PHASE" ]; then
    echo "$CURRENT_PHASE" > "$LAST_PHASE_FILE"
    if [ -z "$LAST_PHASE" ]; then
        echo "Phase detected: $CURRENT_PHASE. Remember to log any methodological decisions to docs/decisions/ using the ADR template (0000-template.md)."
    else
        echo "Phase transition detected ($LAST_PHASE -> $CURRENT_PHASE). Remember to log any methodological decisions to docs/decisions/ using the ADR template (0000-template.md)."
    fi
fi
