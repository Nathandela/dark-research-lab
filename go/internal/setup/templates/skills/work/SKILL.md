---
name: Work
description: Route work tasks to the appropriate sub-skill based on task context
phase: work
---

# Work Router

## Overview

Generic work framework that reads task context and delegates to the right sub-skill(s). The router picks tasks, detects the work mode, and hands off to `work-code`, `work-writing`, or `work-analysis`.

## Methodology

### Step 1: Pick and Claim Tasks

1. Run `bd ready` to find available tasks (or use the task ID from arguments)
2. Claim: `bd update <id> --claim`
3. Read epic context: `bd show <epic>` for the spec, acceptance criteria table, and verification contract
4. Run `drl search` for relevant context from prior work

### Step 2: Detect Work Mode

Read the task title and description. Match keywords to determine the sub-skill:

| Keywords | Sub-Skill |
|----------|-----------|
| implement, test, code, function, module, fix bug, refactor, pipeline | `work-code/SKILL.md` |
| write, draft, section, introduction, discussion, prose, abstract, conclusion | `work-writing/SKILL.md` |
| regression, analysis, table, figure, descriptive stats, robustness, estimate | `work-analysis/SKILL.md` |

If the task is ambiguous (no clear keyword match), use `AskUserQuestion` to clarify the work mode.

### Step 3: Execute Sub-Skill

1. **Read the selected sub-skill file** (`.claude/skills/drl/<sub-skill>/SKILL.md`) and follow its instructions
2. For composite tasks (e.g., "run regression and write results section"):
   - Run `work-analysis` first to produce tables and figures
   - Then run `work-writing` to draft the section referencing those outputs
3. Pass the task context (epic, acceptance criteria, plan equations) to the sub-skill

### Step 4: Decision Logging

Every methodological choice MUST be logged to `docs/decisions/` using the ADR template (`docs/decisions/0000-template.md`). Use `/drl:decision` for guided logging. This applies regardless of which sub-skill executes the work.

### Step 5: Close Tasks

1. Verify all acceptance criteria are met
2. Update task notes: `bd update <id> --notes="Completed: ..."`
3. Close: `bd close <id>`

## Gate Criteria

**Gate 3: All Work Tasks Closed**

| Criterion | Verification |
|-----------|-------------|
| All work tasks closed | `bd list --status=in_progress` is empty |
| Sub-skill gates pass | Each invoked sub-skill's verification gate passes |
| All decisions logged | `ls docs/decisions/` (one ADR per decision) |
| Spec was approved | `bd show <epic>` confirms spec phase complete |

## Memory Integration

- `drl search` before each task for relevant patterns
- `drl learn` after discoveries or corrections

## Common Pitfalls

- Not reading the sub-skill file before executing (skipping delegation)
- Wrong mode detection: a "write regression code" task is code, not analysis
- Skipping decision logging for "minor" choices
- Running writing before analysis outputs exist
- Not verifying the spec was approved before starting work
