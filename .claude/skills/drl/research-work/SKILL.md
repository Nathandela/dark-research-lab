---
name: Research Work
description: Execute analysis pipeline, generate tables and figures, write paper sections, and auto-log decisions
phase: work
---

# Research Work Skill

## Overview

Execute the approved research plan. Run the statistical analysis pipeline, produce publication-ready tables and figures, write paper sections, and auto-log all methodological decisions. This phase turns the plan into concrete research outputs.

## Input

- Approved research plan from the plan phase
- Beads tasks: `bd ready` for analysis tasks to execute
- Variable operationalization table and model equations from the plan
- Hypothesis-analysis-output-section mapping

## Methodology

### Step 1: Claim and Organize Work

1. Run `bd ready` to find available analysis tasks
2. Claim tasks: `bd update <id> --claim`
3. Read the parent epic (`bd show <epic>`) for EARS requirements and the research plan
4. **Verify spec approval** (hard check): Run `bd show <epic>` and confirm the spec phase status is complete. Look for spec-phase closure or notes confirming approval. If the spec phase is not complete, do NOT proceed -- flag the blocker via `AskUserQuestion`

### Step 2: Execute Analysis Pipeline

Spawn **analyst** subagent (`.claude/agents/drl/analyst.md`) for each analysis task:

1. **Data loading and cleaning** (`src/data/`):
   - Load raw data using `src/data/loaders.py`
   - Apply cleaning rules from `src/data/cleaners.py`
   - Validate against the operationalization table
   - Write analysis-ready datasets

2. **Descriptive statistics** (`src/analysis/descriptive.py`):
   - Summary statistics (mean, sd, min, max, N)
   - Correlation matrices
   - Distribution checks
   - Output to `paper/outputs/tables/`

3. **Main regressions** (`src/analysis/econometrics.py`):
   - Implement each model equation from the plan
   - Follow variable operationalization exactly
   - Output regression tables to `paper/outputs/tables/`
   - Output figures to `paper/outputs/figures/`

4. **Robustness checks** (`src/analysis/robustness.py`):
   - Execute the robustness plan from the plan phase
   - Run alternative specifications
   - Output robustness tables to `paper/outputs/tables/`

### Step 3: Write Paper Sections

For each section in the hypothesis-analysis-output-section mapping:

1. Write LaTeX content to `paper/sections/{section}.tex`
2. Reference the generated tables and figures
3. Interpret results in the context of the hypotheses
4. Flag any unexpected findings for human review

Paper section files:
- `paper/sections/data.tex` -- sample description, descriptive stats
- `paper/sections/results.tex` -- main findings per hypothesis
- `paper/sections/robustness.tex` -- alternative specification results

### Step 4: Auto-Log Decisions

Every methodological choice made during execution MUST be logged:

1. Create an ADR in `docs/decisions/` using the template (`docs/decisions/0000-template.md`)
2. Log decisions including:
   - Variable transformations applied
   - Outlier handling choices
   - Sample exclusion decisions
   - Estimation method refinements
   - Any deviation from the original plan
3. Use sequential numbering: check existing ADRs and increment

### Step 5: Agent Progress Notes

Throughout execution, maintain progress visibility:

1. Update beads task notes: `bd update <id> --notes="Progress: ..."`
2. Flag blockers immediately: unexpected data quality issues, failed assumptions
3. If a planned analysis cannot proceed as specified, stop and use `AskUserQuestion`

## Gate Criteria

**Gate: All Analyses Complete**

Before proceeding to methodology-review, verify ALL of:

| Criterion | Verification |
|-----------|-------------|
| All analysis tasks executed | `bd list --status=open` shows no analysis tasks |
| Tables generated | `ls paper/outputs/tables/` |
| Figures generated | `ls paper/outputs/figures/` |
| Paper sections written | `ls paper/sections/*.tex` |
| All decisions logged as ADRs | `ls docs/decisions/` (one per decision) |
| No tasks in-progress | `bd list --status=in_progress` is empty |
| Tests pass | `uv run python -m pytest` |
| Spec was approved | `bd show <epic>` confirms spec phase complete |

## Memory Integration

- `drl search` before each analysis task for relevant patterns
- `drl learn` after corrections, unexpected results, or novel findings
- Log progress notes to beads tasks

## Failure and Recovery

If the work phase fails mid-execution:

1. **Analysis code fails** (runtime errors, data issues):
   - Check data loading and cleaning steps first
   - Verify variable operationalization matches the plan
   - Log any data issues discovered to `docs/decisions/`
   - Fix and re-run -- do not skip failed analyses

2. **Tests fail** (`uv run python -m pytest` returns errors):
   - Read the test output and fix the failing tests or the code they exercise
   - Do not proceed to review with failing tests

3. **Unexpected results** (sign flips, non-significance):
   - Do NOT discard or hide unfavorable results
   - Log the unexpected finding to `docs/decisions/`
   - Flag for human review via `AskUserQuestion`
   - Report all results in the paper, including unexpected ones

4. **Partial completion** (some tasks done, agent interrupted):
   - Check `bd list --status=in_progress` for unfinished tasks
   - Resume from the last incomplete task -- completed work is preserved in `paper/outputs/`

## Common Pitfalls

- Running analyses without verifying the research spec was approved
- Not following the variable operationalization table exactly
- Forgetting to log decisions as ADRs
- Modifying the analysis plan without documenting the change
- Generating tables without proper labels, units, or source notes
- Not flagging unexpected results for human review
- Fabricating or simulating data in production code

## Quality Criteria

- [ ] Analysis code is testable (functions in `src/`, not scripts)
- [ ] Analyst subagent executed analysis per the plan
- [ ] All outputs in correct directories (`paper/outputs/tables/`, `paper/outputs/figures/`)
- [ ] Results are reproducible (fixed seeds, documented transforms)
- [ ] Paper sections reference generated outputs
- [ ] Every decision logged to `docs/decisions/`
- [ ] Agent progress notes maintained in beads
- [ ] All tests pass
