---
name: Work Analysis
description: Execute statistical analysis pipeline, generate tables and figures
---

# Work Analysis Sub-Skill

## Overview

Run the analysis pipeline from data to outputs. Every result must be reproducible -- fixed seeds, documented transformations, and a reproducibility manifest. This sub-skill is invoked by the work router -- it does not run standalone.

## Agent Delegation

Deploy analysis agents:

- **Analyst**: `.claude/agents/drl/analyst.md` -- executes regressions and generates outputs
- **Data-quality-reviewer**: validates data integrity before analysis
- **Robustness-checker**: runs alternative specifications and sensitivity checks

## Methodology

### Step 1: Understand the Task

1. Read the task description and the research plan's model equations
2. Identify which analyses are required (descriptive, main regressions, robustness)
3. Check `bd show <epic>` for the variable operationalization table

### Step 2: Load and Clean Data

1. Load raw data using `src/data/loaders.py`
2. Apply cleaning rules from `src/data/cleaners.py`
3. Validate against the operationalization table
4. Write analysis-ready datasets

### Step 3: Run Analysis Pipeline

Execute in order, outputting to `paper/outputs/tables/` and `paper/outputs/figures/`:

1. **Descriptive statistics** (`src/analysis/descriptive.py`): summary stats, correlations, distributions
2. **Main regressions** (`src/analysis/econometrics.py`): implement each model equation per the plan, follow variable operationalization exactly
3. **Robustness battery** (`src/analysis/robustness.py`): alternative specifications, sensitivity analyses

### Step 4: Log All Decisions

Log ALL methodological decisions to `docs/decisions/` using the ADR template:

- Variable exclusions or transformations
- Winsorization or outlier handling choices
- Sample restrictions applied
- Any deviation from the original plan

Use `/drl:decision` for guided logging.

### Step 5: Update Reproducibility Manifest

```bash
uv run python -m src.orchestrators.repro
```

## Verification Gate

- Reproducibility manifest updated
- Output tables exist in `paper/outputs/tables/`
- Output figures exist in `paper/outputs/figures/`
- All analyses from the plan are executed (no skipped models)

## Scope

- Data pipeline: `src/data/`
- Analysis code: `src/analysis/`
- Visualization: `src/visualization/`
- Outputs: `paper/outputs/tables/`, `paper/outputs/figures/`
