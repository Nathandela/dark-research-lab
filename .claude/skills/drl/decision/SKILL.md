---
name: Decision
description: Log methodological decisions to the ADR registry with structured rationale
---

# Decision Logging Skill

## Overview

Record methodological decisions to the Architecture Decision Record (ADR) registry at `docs/decisions/`. Every statistical method choice, data source selection, variable operationalization, and robustness design decision must be logged with structured rationale. This creates a traceable audit trail for the entire research project.

## ADR Template

All decisions follow the template at `docs/decisions/0000-template.md`. Read it before creating a new entry.

### File Naming Convention

Files are named sequentially: `NNNN-slug.md`

- `NNNN`: Four-digit zero-padded number, incrementing from the highest existing number
- `slug`: Lowercase hyphenated summary of the decision (e.g., `use-iv-for-endogeneity`, `exclude-outliers-above-3sd`)

To find the next number:
```bash
ls docs/decisions/[0-9]*.md 2>/dev/null | sort -r | head -1
```

## What Decisions to Log

### Statistical Method Choices
- Estimation method (OLS, IV, DiD, RDD, panel methods, Bayesian)
- Standard error specification (robust, clustered, bootstrapped)
- Multiple testing corrections (Bonferroni, Holm, FDR)
- Model specification (linear, log-linear, nonlinear)

### Data Source Selections
- Why this dataset over alternatives
- Sample period and geographic scope
- Inclusion and exclusion criteria with justification
- Data quality thresholds (e.g., minimum response rate, maximum missing data)

### Variable Operationalization
- How abstract constructs become measurable variables
- Which proxy variables are used and why
- Scaling, transformation, and normalization choices
- Control variable selection rationale

### Robustness Check Design
- Which alternative specifications to run
- Which sensitivity analyses are appropriate
- Placebo test design
- Subsample analysis rationale

## Required Sections in Each ADR

Every decision record must include:

### Context
- What question or problem prompted this decision?
- What phase of the research triggered it?
- What constraints or requirements apply?

### Decision
- What was decided? State it clearly and unambiguously.
- Include the specific method, threshold, or approach chosen.

### Rationale
- Why this choice over alternatives?
- What evidence or literature supports it?
- What assumptions does it rest on?

### Alternatives Considered
- What other options were evaluated?
- Why were they rejected?
- Under what conditions would you reconsider?

### Consequences
- What does this decision enable or constrain?
- What risks does it introduce?
- What follow-up decisions does it trigger?

## Searching Existing Decisions

Before creating a new ADR, search for related existing decisions:

1. List all decisions: `ls docs/decisions/`
2. Search by keyword: `grep -r "keyword" docs/decisions/`
3. Check for superseded decisions that this one might update

If a new decision changes a prior one, update the old ADR status to "superseded" and reference the new ADR.

## Workflow Integration

Decision logging integrates with every research phase:

- **Specification phase**: Log RQ formulation choices, hypothesis framing decisions
- **Planning phase**: Log method selections, identification strategy, variable operationalization
- **Work phase**: Log deviations from plan, post-hoc analytical decisions, data cleaning choices
- **Review phase**: Log corrections prompted by reviewer findings
- **Synthesis phase**: Log final presentation choices, contribution framing

When running `/drl:cook-it`, the orchestrator prompts for decision logging at each phase transition.

## Gate Criteria

For each decision entry, verify:
- [ ] Sequential number is correct (no gaps, no duplicates)
- [ ] All five sections are present (context, decision, rationale, alternatives, consequences)
- [ ] Rationale references evidence or literature (not just preference)
- [ ] Alternatives are genuine options, not strawmen
- [ ] File is saved to `docs/decisions/NNNN-slug.md`

## Common Pitfalls

- Logging decisions after the fact without the original reasoning context
- Writing vague rationale ("it seemed best") without evidence
- Not recording alternatives that were seriously considered
- Creating decisions that duplicate or contradict existing ADRs
- Forgetting to log data cleaning decisions (which often have large methodological impact)
- Not updating superseded decisions when methodology changes
