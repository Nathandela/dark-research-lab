---
name: Test Cleaner
description: Multi-phase research test suite optimization with adversarial review for reproducibility and statistical correctness
phase: review
---

# Test Cleaner Skill

## Overview
Analyze, optimize, and clean a research project's test suite through a multi-phase workflow with adversarial review. Focuses on reproducibility tests, data validation coverage, statistical correctness checks, and analysis pipeline tests. Produces machine-readable output and feeds findings into DRL memory.

## Methodology

### Phase 1: Analysis
Spawn multiple analysis subagents in parallel:
- **Cargo-cult detector**: Find fake tests, mocked data that hides real data issues, trivial assertions (e.g., `assert True`), tests that pass regardless of input
- **Reproducibility checker**: Verify tests pin random seeds, lock dependencies, and produce deterministic outputs from the same inputs
- **Data validation auditor**: Check that tests validate data schemas, missing values, type constraints, range boundaries, and exclusion criteria
- **Statistical test auditor**: Verify that tests check estimation outputs for expected properties (coefficient signs, standard error positivity, convergence, degree-of-freedom counts)
- **Pipeline coverage analyzer**: Map which pipeline stages (`src/data/` loading, `src/analysis/` estimation, `paper/outputs/` generation) have test coverage and which do not

### Phase 2: Planning
Synthesize analysis results into a refined optimization plan:
- Categorize findings by severity (P1/P2/P3)
- Propose specific changes for each finding
- Estimate impact on reproducibility confidence and pipeline reliability
- Iterate with subagents until the plan is comprehensive

### Phase 3: Adversarial Review (CRITICAL QUALITY GATE)
**This is THE KEY PHASE -- the most important phase in the entire workflow. NEVER skip, NEVER rush, NEVER settle for "good enough."**

Expose the plan to two neutral reviewer subagents:
- **Reviewer A** (Opus): Independent critique focusing on statistical validity and reproducibility
- **Reviewer B** (Sonnet): Independent critique focusing on data integrity and pipeline coverage

Both reviewers challenge assumptions, identify risks, and suggest improvements.

**Mandatory iteration loop**: After each reviewer pass, if ANY issues, concerns, or suggestions remain from EITHER reviewer, revise the plan and re-submit to BOTH reviewers. Repeat until BOTH reviewers explicitly approve with ZERO reservations. Do not proceed to Phase 4 until unanimous, unconditional approval is reached.

### Phase 4: Execution
Apply the agreed changes:
- Machine-readable output format: `ERROR [file:line] type: description`
- Include `REMEDIATION` suggestions and `SEE` references
- Run targeted test validation: `uv run python -m pytest tests/<module> -v`

### Phase 5: Verification
- Run full test suite: `uv run python -m pytest`
- Compare before/after metrics (test count, duration, coverage)
- Verify reproducibility: run pipeline twice and compare outputs
- Feed findings into DRL memory via `drl learn`

## Research-Specific Test Categories

### Data Validation Tests
- Schema enforcement (column names, types, expected ranges)
- Missing value handling (detection, imputation verification, listwise deletion counts)
- Sample restriction tests (exclusion criteria applied correctly)
- Data provenance checks (source file checksums, expected row counts)

### Statistical Correctness Tests
- Coefficient sign tests for known relationships
- Standard error positivity and reasonableness
- Convergence verification for iterative estimators
- Degree-of-freedom accounting
- Known-answer tests against published replication results

### Pipeline Integration Tests
- End-to-end: raw data to final table/figure output
- Output file existence and format validation (`paper/outputs/tables/*.tex`, `paper/outputs/figures/*.pdf`)
- LaTeX compilation after output generation
- Deterministic output: same input produces identical output across runs

### Reproducibility Tests
- Random seed pinning verification
- Environment reproducibility (dependency versions match `uv.lock`)
- Cross-platform consistency where applicable

## Memory Integration
- Run `drl search "test optimization"` before starting
- After completion, capture findings via `drl learn`

## Common Pitfalls
- Deleting tests without verifying the invariant is covered elsewhere
- Optimizing for speed at the cost of reproducibility coverage
- Settling for partial approval or cutting the Phase 3 review loop short
- Not testing data validation (the most common source of silent research errors)
- Writing tests that mock away the data layer entirely, hiding real data issues
- Ignoring determinism: tests that pass sometimes but fail on re-runs indicate seed or ordering problems

## Quality Criteria
- All 5 phases completed (analysis, planning, review, execution, verification)
- Both adversarial reviewers approved with zero reservations after iterative refinement
- Machine-readable output format used throughout
- Full test suite passes after changes: `uv run python -m pytest`
- Data validation coverage not degraded
- Reproducibility verified (pipeline produces identical output on re-run)
- Findings captured in DRL memory via `drl learn`
