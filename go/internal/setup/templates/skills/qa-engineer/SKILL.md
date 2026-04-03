---
name: QA Engineer
description: Hands-on QA of the research analysis pipeline. Use whenever the user asks to verify the pipeline end-to-end, check output file integrity, validate table and figure generation, test data processing, or verify LaTeX compilation. Triggers on phrases like "test the pipeline", "QA the analysis", "check the outputs", "verify the tables", "run end-to-end", "does the paper compile", or any request to validate a research pipeline.
phase: review
---

# QA Engineer Skill

## Overview

Perform hands-on quality assurance against a research analysis pipeline. This skill covers what automated unit tests miss: end-to-end pipeline execution, output file integrity, table and figure validation, data pipeline correctness, and LaTeX compilation verification. The output is a structured QA report with P0-P3 findings.

The skill works by executing the analysis pipeline, inspecting generated outputs, and verifying the compiled paper. Think of it as a systematic research assistant who checks that everything actually works.

## Decision Tree

```
User task --> What type of target?
|
+-- Full pipeline --> Run end-to-end from raw data to compiled PDF
|   1. Execute data processing scripts
|   2. Run analysis/estimation code
|   3. Verify output generation (tables, figures)
|   4. Compile LaTeX paper
|   5. Cross-check outputs against paper references
|
+-- Data pipeline only --> Data Reconnaissance
|   1. Verify raw data files exist and are readable
|   2. Run data processing scripts
|   3. Check output schemas and row counts
|   4. Validate against data dictionary
|
+-- Paper compilation only --> LaTeX Verification
|   1. Run drl:compile
|   2. Check for unresolved references
|   3. Verify all tables/figures render
|   4. Report warnings and errors
|
+-- No pipeline scripts found --> SKIP
    Report: "QA Engineer skipped: no analysis pipeline detected"
```

## Phase 1: Environment Verification

Before running anything, verify the research environment is ready.

**Check in order:**
1. Python environment exists and dependencies are installed: `uv sync`
2. Raw data files are present (check paths referenced in analysis scripts)
3. Required directories exist: `src/data/`, `src/analysis/`, `paper/outputs/tables/`, `paper/outputs/figures/`
4. LaTeX toolchain is available: `command -v pdflatex` or `command -v latexmk`
5. All analysis entry points are executable

**If environment fails**: Report **P1/INFRA** with specific missing components and remediation steps. Do not proceed until the environment is functional.

## Phase 2: Pipeline Reconnaissance

Before testing, understand the pipeline structure:

1. **Scan** `src/data/` for data processing scripts -- identify execution order
2. **Scan** `src/analysis/` for estimation and analysis scripts
3. **Check** `Makefile`, `pyproject.toml` scripts, or pipeline entry points for documented execution order
4. **List** expected outputs in `paper/outputs/tables/` and `paper/outputs/figures/`
5. **Read** `paper/main.tex` to identify which tables and figures are referenced via `\input` and `\includegraphics`
6. **Report** discovered pipeline structure before proceeding

## Phase 3: Pipeline Execution and Validation

Execute the pipeline and validate each stage. Select strategies based on what reconnaissance discovered.

### Strategy 1: Data Pipeline Validation
- Execute data processing scripts in order
- Verify output files are created with expected schemas
- Check row counts against documented expectations
- Validate no silent data loss (input rows vs. output rows, with exclusions accounted for)
- Check for unexpected NaN/null values in key variables

### Strategy 2: Analysis Pipeline Validation
- Execute estimation scripts
- Verify output files are created in `paper/outputs/tables/` and `paper/outputs/figures/`
- Check that tables contain expected columns (coefficients, standard errors, statistics)
- Check that figures are valid files (PDF not empty, correct dimensions)
- Verify log files or console output show convergence (no warnings about non-convergence)

### Strategy 3: Output Integrity Check
- Every file in `paper/outputs/tables/` is valid LaTeX (no syntax errors)
- Every file in `paper/outputs/figures/` is a valid image/PDF
- File sizes are reasonable (not 0 bytes, not suspiciously large)
- Table values are in plausible ranges (no coefficients of 10^15, no negative R-squared)

### Strategy 4: LaTeX Compilation
- Run `drl:compile` or `latexmk -pdf paper/main.tex`
- Check for errors (missing files, undefined references, missing citations)
- Verify all `\input{outputs/tables/...}` resolve to existing files
- Verify all `\includegraphics{outputs/figures/...}` resolve to existing files
- Check for overfull/underfull box warnings (potential formatting issues)

### Strategy 5: Cross-Reference Validation
- Every table referenced in the text (`Table \ref{...}`) exists and renders
- Every figure referenced in the text (`Figure \ref{...}`) exists and renders
- Numbers cited in the prose (e.g., "coefficient of 0.42") match the corresponding table cell
- All `\cite{}` commands resolve to entries in the bibliography
- No orphaned outputs (files in `paper/outputs/` not referenced anywhere in the paper)

### Strategy 6: Reproducibility Spot-Check
- Run the pipeline twice and compare outputs
- Check if table values are identical across runs (determinism)
- If differences exist, check whether random seeds are properly pinned
- Verify that `uv.lock` matches installed dependencies

## Phase 4: Report

Produce a structured QA report with findings classified by severity:

```markdown
## QA Report: [Project Name]

**Pipeline**: [description of what was tested]
**Date**: [timestamp]
**Strategies applied**: [list of strategies used]

### P0 Findings (Blocks Publication)
- Pipeline produces incorrect results (wrong data, failed estimation)
- Output files missing or corrupted
- LaTeX compilation fails entirely

### P1 Findings (Critical)
- Non-deterministic outputs (results change between runs)
- Unresolved references or citations in compiled paper
- Data validation failures (unexpected NaN, wrong row counts)
- Analysis convergence warnings

### P2 Findings (Important)
- Numbers in prose do not match table values
- Orphaned outputs (generated but not referenced)
- LaTeX warnings (overfull boxes, missing labels)
- Missing table notes or figure labels

### P3 Findings (Minor)
- Formatting inconsistencies across tables
- Minor LaTeX warnings
- Unused bibliography entries
- Non-critical file naming inconsistencies

### Passed Checks
[List what was tested and passed -- evidence that QA was thorough]
```

Each finding includes: **what** (the problem), **where** (file path and line/cell), **how to reproduce** (command to run), and **severity justification**.

## Phase 5: Cleanup

1. Remove any temporary files created during testing
2. Save the QA report to `docs/qa/` or present inline
3. If pipeline was run, verify working directory is clean (`git status`)

## Integration with Review Phase

When invoked as part of the review skill (not standalone):
- Findings merge into the review's P0-P3 classification
- Communicate findings via `SendMessage` to the review lead
- Follow the same format as other reviewer agents

## Graceful Degradation

| Scenario | Behavior | Severity |
|----------|----------|----------|
| No analysis scripts found | SKIP, report informational | P3/INFO |
| Raw data files missing | Report with paths and remediation | P1/INFRA |
| Python environment broken | Attempt `uv sync`, retry once | P1/INFRA if still fails |
| LaTeX not installed | Skip compilation, report limitation | P2/INFO |
| Pipeline partially fails | Report which stages passed/failed, continue where possible | P1 |
| Reconnaissance finds no outputs directory | Create directories and note in report | P3/INFO |

## Common Pitfalls

- Running analysis without verifying data files exist first
- Not checking output determinism (running only once proves nothing about reproducibility)
- Skipping cross-reference validation (orphaned outputs are a common review finding)
- Testing only the happy path (what happens when a data file is malformed?)
- Reporting formatting issues without checking substantive correctness first
- Not cleaning up temporary files after testing
- Assuming LaTeX compiles if the pipeline runs (they are separate failure modes)

## Quality Criteria

- Environment verified before any pipeline execution
- Reconnaissance completed before testing
- At least data pipeline validation + output integrity check applied
- All findings classified P0-P3 with reproduction commands
- Cross-reference validation performed (text matches tables)
- Reproducibility spot-checked (pipeline run at least twice)
- Passed checks documented (evidence that QA was thorough)
- Temporary files cleaned up after testing
- Report is actionable (each finding has enough detail to fix)
