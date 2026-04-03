---
name: Cook It
description: Orchestrate the full DRL research workflow from specification through paper synthesis
---

# DRL Research Workflow Orchestrator

## Overview

Run the complete DRL research pipeline for a given epic. This is the DRL cook-it workflow, adapting the compound cook-it pattern for social science research. It chains five research phases in sequence, enforcing gate criteria between each transition. Each phase uses a dedicated DRL skill and involves specialized research agents.

## Prerequisites

Before running cook-it, verify these dependencies are in place:

1. **Hooks configured** in `.claude/settings.json`:
   - `UserPromptSubmit` must include `decision-reminder.sh` (ADR reminders on phase transitions)
   - `PreToolUse` must include `phase-guard` (prevents writes during wrong phase)
   - Verify: `cat .claude/settings.json | python3 -c "import json,sys; h=json.load(sys.stdin)['hooks']; assert any('decision-reminder' in hook['command'] for entry in h['UserPromptSubmit'] for hook in entry['hooks']), 'Missing decision-reminder hook'; print('OK: hooks configured')"`

2. **Hook script** exists and is executable:
   - `scripts/hooks/decision-reminder.sh` must be present and executable
   - Verify: `test -x scripts/hooks/decision-reminder.sh && echo 'OK: hook executable'`

3. **ADR template** exists:
   - `docs/decisions/0000-template.md` must be present
   - Verify: `test -f docs/decisions/0000-template.md && echo 'OK: template exists'`

4. **Beads** is initialized:
   - An epic must exist in beads for the research project
   - Verify: `bd show <epic-id>`

## State File Schema: `.drl-phase-state.json`

The cook-it workflow tracks its state in `.claude/.drl-phase-state.json`. This file is the coordination point between the orchestrator and the decision-reminder hook.

| Field | Type | Valid Values | Description |
|-------|------|--------------|-------------|
| `cookit_active` | bool | `true` / `false` | Whether a cook-it session is currently running |
| `current_phase` | string | `"spec"`, `"plan"`, `"work"`, `"review"`, `"synthesis"` | The active workflow phase |
| `epic_id` | string | A beads issue ID (e.g. `"dark-research-lab-xxx"`) | The bead ID of the parent epic |

**Who creates it**: The cook-it orchestrator creates and updates this file at each phase transition.
**Who reads it**: `decision-reminder.sh` reads it on every `UserPromptSubmit` to detect phase changes and emit ADR reminders. The `phase-guard` hook reads it to restrict file writes to the current phase's scope.
**Lifecycle**: Created when cook-it starts, updated at each phase transition, and should be deleted (or set `cookit_active: false`) when the session ends. The companion file `.claude/.drl-last-phase` is automatically cleaned up by `decision-reminder.sh` when it detects `cookit_active` is `false`.

## Input

- Epic ID (from beads) or a research question to start from
- If no epic exists, recommend running `/drl:architect` first to decompose the question into epics

## The Research Phases

### Phase 0: Architecture (research-architect)

**Skill**: `.claude/skills/drl/research-architect/SKILL.md`

**When to use**: Before starting cook-it, if no epic exists yet. `/drl:architect` is the entry point that decomposes a research question into cook-it-ready epics. If the epic already exists with a well-formed description (Scope, EARS, Contracts, Assumptions, Roles, Decisions sections), skip Phase 0 and begin at Phase 1.

**What happens**:
- Refine the research question via Socratic dialogue
- Decompose into naturally-scoped epic beads
- Wire dependencies between epics

This phase is a prerequisite, not part of the cook-it loop itself. Cook-it operates on a single epic produced by the architect.

### Phase 1: Specification (research-spec)

**Skill**: `.claude/skills/drl/research-spec/SKILL.md`

**What happens**:
- Refine the research question into a precise formulation
- Generate testable hypotheses with theoretical grounding
- Survey indexed literature to identify the gap
- Produce a methodology outline (not the full plan)
- Build a domain glossary of key constructs

**Agents involved**: literature-analyst (for gap identification)

**Decision logging**: Log the final research question formulation and hypothesis choices to `docs/decisions/`

**Gate 1**: Research question approved, hypotheses articulated, literature gap documented. Human confirmation via `AskUserQuestion`.

### Phase 2: Planning (research-plan)

**Skill**: `.claude/skills/drl/research-plan/SKILL.md`

**What happens**:
- Design the full analytical methodology
- Specify the identification strategy for causal claims
- Define the variable operationalization (how constructs become measurable)
- Plan the robustness battery (alternative specifications, sensitivity checks)
- Create beads subtasks for each analysis step

**Agents involved**: methodology-reviewer (for plan validation)

**Decision logging**: Log statistical method choices, variable operationalization decisions, and robustness check design to `docs/decisions/`

**Gate 2**: Methodology is sound, identification strategy is defensible, robustness battery is planned. Human confirmation via `AskUserQuestion`.

### Phase 3: Work (research-work)

**Skill**: `.claude/skills/drl/research-work/SKILL.md`

**What happens**:
- Execute the analysis plan: data cleaning, transformation, modeling
- Generate tables and figures to `paper/outputs/tables/` and `paper/outputs/figures/`
- Write results interpretation in paper sections
- Run the robustness battery and report all results (including unfavorable ones)
- Close beads subtasks as each analysis step completes

**Agents involved**: analyst (execution), robustness-checker (robustness battery)

**Decision logging**: Log any deviations from the plan, unexpected findings, and post-hoc decisions to `docs/decisions/`

**Gate 3**: All planned analyses complete, tables and figures generated, results written. All work subtasks closed in beads.

### Phase 4: Review (methodology-review)

**Skill**: `.claude/skills/drl/methodology-review/SKILL.md`

**What happens**:
- Six parallel reviewers audit the completed work:
  1. Statistical validity (methodology-reviewer)
  2. Robustness assessment (robustness-checker)
  3. Logical consistency (coherence-reviewer)
  4. Citation accuracy (citation-checker)
  5. Reproducibility (reproducibility-verifier)
  6. Writing quality (writing-quality-reviewer)
- Findings classified by severity: critical, major, minor
- Critical and major findings must be resolved before proceeding

**Decision logging**: Log any methodological corrections and their rationale to `docs/decisions/`

**Gate 4**: No critical or major findings remain. All six review dimensions pass.

### Phase 5: Synthesis (synthesis)

**Skill**: `.claude/skills/drl/synthesis/SKILL.md`

**What happens**:
- Verify cross-section coherence (the paper tells one story)
- Clarify the contribution statement
- Review the decision log for completeness
- Compile the LaTeX paper via `paper/compile.sh`
- Verify all references resolve (no undefined refs or missing citations)
- Extract lessons for future research cycles

**Agents involved**: writing-quality-reviewer, citation-checker, coherence-reviewer

**Decision logging**: Log any final methodological reflections to `docs/decisions/`

**Gate 5**: Paper compiles cleanly, all references resolve, decision log is complete. Epic closed in beads.

## Phase Transition Protocol

Between each phase:
1. Verify the current phase gate criteria are met
2. Use `AskUserQuestion` to get human approval before proceeding
3. Update the beads epic status
4. Search memory (`drl search`) for relevant context entering the next phase
5. Log any phase-transition decisions to `docs/decisions/` using the ADR template (`docs/decisions/0000-template.md`). Use `/drl:decision` for guided logging

**Decision logging hook**: The `decision-reminder.sh` hook fires automatically on UserPromptSubmit when a phase transition is detected. It reads `.claude/.drl-phase-state.json` to track the current phase and emits a reminder to log decisions to `docs/decisions/`. This is a shell hook, not an orchestrator prompt -- it runs automatically without agent action.

## Phase Failure Recovery

When a phase fails mid-execution:

1. **Save state**: Write current progress to `.drl-phase-state.json` and update the beads task notes with what completed
2. **Log partial decisions**: Any methodological decisions made before the failure must still be logged to `docs/decisions/` using the ADR template (`docs/decisions/0000-template.md`). Use `/drl:decision` for guided logging
3. **Create a recovery bead task**: `bd create --title="Recovery: <phase> phase interrupted" --description="<what was completed, what remains>" --type=task --priority=1`
4. **Resume guidance**: On next `cook-it` invocation:
   - Read `.drl-phase-state.json` to determine the interrupted phase
   - Check `bd list --status=in_progress` for the recovery task
   - Resume from the last incomplete step (completed work is preserved)
   - Do not re-run steps that completed successfully

## Beads Integration

- Track progress via `bd show <epic-id>` at each phase
- Close subtasks as they complete: `bd close <task-id>`
- Create new tasks if unexpected work emerges: `bd create --title="..." --parent=<epic-id>`
- Check for blocked work: `bd blocked`

## Memory Integration

- `drl search` at the start of each phase
- `drl knowledge` for literature context throughout
- `drl learn` after corrections, discoveries, or phase completions

## Common Pitfalls

- Skipping the specification phase and jumping to analysis
- Not enforcing gate criteria between phases (letting problems accumulate)
- Forgetting to log decisions at each phase transition
- Not running the full review fleet (shortcutting to synthesis)
- Proceeding past the review phase with unresolved critical findings
- Not checking beads status before phase transitions
