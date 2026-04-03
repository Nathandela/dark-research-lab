#!/bin/bash
# decision-reminder.sh - Advisory reminder to log methodological decisions
# Fires on UserPromptSubmit when cook-it is active
#
# .ca-phase-state.json format:
#   cookit_active  (bool)   - whether a cook-it session is running
#   current_phase  (string) - active workflow phase (e.g. "spec-dev", "analysis")
#   epic_id        (string) - bead ID of the parent epic
#
# .drl-last-phase lifecycle:
#   Tracks the last seen phase to detect phase transitions.
#   Created on first phase detection, updated on each transition,
#   and deleted when cook-it session ends (cookit_active becomes false).

REPO_ROOT="${DRL_REPO_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}"
PHASE_STATE="$REPO_ROOT/.claude/.ca-phase-state.json"
LAST_PHASE_FILE="$REPO_ROOT/.claude/.drl-last-phase"

# Exit silently if no phase state (not in cook-it)
[ -f "$PHASE_STATE" ] || exit 0

# Read cookit_active and current_phase
PHASE_DATA=$(python3 -c "
import json, sys
try:
    with open(sys.argv[1]) as f:
        state = json.load(f)
    active = '1' if state.get('cookit_active') else '0'
    phase = state.get('current_phase', '')
    print(active)
    print(phase)
except Exception:
    print('0')
    print('')
" "$PHASE_STATE" 2>/dev/null)

COOKIT_ACTIVE=$(echo "$PHASE_DATA" | head -1)
CURRENT_PHASE=$(echo "$PHASE_DATA" | tail -1)

# If cook-it is not active, clean up .drl-last-phase and exit
if [ "$COOKIT_ACTIVE" != "1" ]; then
    [ -f "$LAST_PHASE_FILE" ] && rm -f "$LAST_PHASE_FILE"
    exit 0
fi

# Exit if no phase detected
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
