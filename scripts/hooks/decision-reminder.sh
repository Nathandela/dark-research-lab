#!/bin/bash
# decision-reminder.sh - Advisory reminder to log methodological decisions
# Fires on UserPromptSubmit when cook-it is active

PHASE_STATE=".claude/.ca-phase-state.json"
LAST_PHASE_FILE=".claude/.drl-last-phase"

# Exit silently if no phase state (not in cook-it)
[ -f "$PHASE_STATE" ] || exit 0

# Read current phase
CURRENT_PHASE=$(python3 -c "
import json, sys
try:
    with open('$PHASE_STATE') as f:
        state = json.load(f)
    if state.get('cookit_active'):
        print(state.get('current_phase', ''))
except Exception:
    pass
" 2>/dev/null)

# Exit if not in active cook-it
[ -z "$CURRENT_PHASE" ] && exit 0

# Read last known phase
LAST_PHASE=""
[ -f "$LAST_PHASE_FILE" ] && LAST_PHASE=$(cat "$LAST_PHASE_FILE")

# If phase changed, emit reminder
if [ "$CURRENT_PHASE" != "$LAST_PHASE" ]; then
    echo "$CURRENT_PHASE" > "$LAST_PHASE_FILE"
    echo "Phase transition detected ($LAST_PHASE -> $CURRENT_PHASE). Remember to log any methodological decisions to docs/decisions/ using the ADR template (0000-template.md)."
fi
