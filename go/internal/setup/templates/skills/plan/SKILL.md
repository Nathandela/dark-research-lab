---
name: Research Plan
description: Specify statistical methodology, variable operationalization, model equations, robustness plan, and hypothesis-to-section mapping
phase: plan
---

# Research Plan Skill

## Overview

Translate the approved research specification into a concrete analysis plan. Define exactly how each hypothesis will be tested: which variables, which models, which robustness checks, and which paper section reports each result.

## Input

- Approved research spec from the spec phase
- Beads epic: `bd show <epic-id>` for scope and EARS requirements
- Literature context: `drl knowledge` for methodological precedent

## Methodology

### Step 1: Variable Operationalization

1. For each construct in the domain glossary, define:
   - **Operational definition**: How it is measured (exact formula, scale, coding)
   - **Data source**: Where the raw values come from
   - **Transformations**: Log, standardize, winsorize, categorical encoding
   - **Missing data strategy**: Listwise deletion, imputation, or exclusion criteria
2. Produce a **variable operationalization table**:

| Variable | Construct | Source | Measurement | Transform | Missing Strategy |
|----------|-----------|--------|-------------|-----------|------------------|
| ...      | ...       | ...    | ...         | ...       | ...              |

### Step 2: Model Equations

1. Write out the statistical model(s) formally:
   - Dependent variable(s)
   - Independent variables and controls
   - Functional form (linear, logistic, panel, etc.)
   - Estimation method (OLS, IV, MLE, etc.)
2. For each equation, note:
   - Which hypothesis it tests
   - Key identifying assumptions
   - Expected coefficient signs

### Step 3: Robustness Plan

1. For each main specification, plan at least two alternative specifications:
   - Alternative variable operationalizations
   - Alternative sample restrictions (trimming, subgroup analysis)
   - Alternative estimation methods
2. Plan diagnostic checks:
   - Multicollinearity (VIF)
   - Heteroscedasticity tests
   - Normality of residuals (where relevant)
   - Influence diagnostics (Cook distance, leverage)
3. Plan falsification or placebo tests where applicable

### Step 4: Hypothesis-Analysis-Output-Section Mapping

Create a traceability table linking each hypothesis to its analysis pipeline and paper output:

| Hypothesis | Model | Key Variables | Output Table/Figure | Paper Section |
|------------|-------|---------------|---------------------|---------------|
| H1         | Eq. 1 | X1, X2       | Table 1             | results.tex   |
| H2         | Eq. 2 | X1, Z1       | Table 2, Figure 1   | results.tex   |
| ...        | ...   | ...           | ...                 | robustness.tex|

This mapping ensures every hypothesis has a clear path through the analysis pipeline to a paper section.

### Step 5: Analysis Task Breakdown

1. Decompose the plan into implementable tasks:
   - Data loading and cleaning
   - Descriptive statistics
   - Main regressions (one per hypothesis)
   - Robustness checks
   - Figure generation
2. Create beads tasks: `bd create --title="..." --type=task --priority=<N>`
3. Wire dependencies: data cleaning before analysis, analysis before robustness

## Gate Criteria

**Gate 2: Methodology Approved**

Before proceeding to research-work, verify ALL of:

| Criterion | Verification |
|-----------|-------------|
| Variable operationalization table is complete | Table must include columns: Variable, Construct, Source, Measurement, Transform, Missing Strategy. At least one row per hypothesis variable |
| Model equations formally specified | Each equation must name DV, IV(s), functional form, and estimation method |
| Robustness plan covers at least 2 alternatives per main spec | Count alternative specifications in plan: minimum 2 per main model |
| Hypothesis-analysis-output-section mapping complete | Every H row must have a non-empty Model, Output Table/Figure, and Paper Section cell |
| Analysis tasks created as beads with deps | `bd list --status=open` returns >= 1 analysis task and `bd show <task>` shows wired dependencies |

Use `AskUserQuestion` to confirm the methodology with the researcher before proceeding.


## Handoff Checklist

| Output | Location | Format | Next Phase Retrieval |
|--------|----------|--------|---------------------|
| Variable operationalization table | Plan document or `docs/specs/<topic>.md` | Markdown table: Variable / Construct / Source / Measurement / Transform / Missing Strategy | research-work reads the plan to map variables to code |
| Model equations | Plan document | Formal equations with DV, IV, functional form, estimation method | research-work implements each equation in `src/analysis/econometrics.py` |
| Robustness plan | Plan document | List of alternative specifications per main model | research-work executes robustness battery from `src/analysis/robustness.py` |
| Hypothesis-analysis-output-section mapping | Plan document | Markdown table: H -> Model -> Variables -> Output Table/Figure -> Paper Section | research-work uses mapping to route outputs to correct files |
| Analysis beads tasks | Beads (`bd list --status=open`) | Task beads with dependencies wired | research-work picks up tasks via `bd ready` |

## Memory Integration

- `drl search` for past methodology decisions in this domain
- `drl knowledge` for statistical methodology references
- `drl learn` after methodology choices are made
- Log each methodological decision to `docs/decisions/` using the ADR template (`docs/decisions/0000-template.md`). Use `/drl:decision` for guided logging

## Failure and Recovery

If the plan phase fails mid-execution:

1. **Methodology reviewer rejects the approach**:
   - Log the rejection rationale to `docs/decisions/`
   - Revise the methodology based on feedback
   - Re-submit for review -- do not skip the gate

2. **Variable operationalization blocked** (data source unavailable):
   - Document the missing data as a beads note
   - Propose alternative operationalizations with available data
   - Log the pivot decision to `docs/decisions/`

3. **Human gate times out**:
   - Save the current plan to the epic description/notes
   - Update beads: `bd update <id> --notes="Plan draft complete, awaiting approval"`

## Common Pitfalls

- Defining variables without specifying the exact measurement
- Missing the hypothesis-to-section traceability chain
- Robustness plan that only tests trivial alternatives
- Not logging methodology decisions as ADRs
- Analysis tasks without proper dependency ordering
- Specifying methods beyond what the data can support

## Quality Criteria

- [ ] Every construct has a concrete operationalization
- [ ] Model equations are written formally, not just described
- [ ] Robustness plan is substantive (not just "run it again")
- [ ] Traceability mapping covers all hypotheses end-to-end
- [ ] Beads tasks created and dependency-ordered
- [ ] Methodology decisions logged to `docs/decisions/`
- [ ] Human approved methodology via gate
