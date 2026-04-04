# Research Onboarding Guide

## What is DRL?

Dark Research Lab (DRL) is a research operating system. It is not a statistical package or a paper template. It is an AI-assisted research workflow that takes you from a research question to a publishable paper through a structured, reproducible pipeline.

DRL provides:
- A multi-phase research cycle with built-in quality gates
- Specialized AI agents for each research task (methodology review, statistical analysis, academic writing)
- Mandatory decision logging for every methodological choice
- A knowledge base of social science methodology that agents reference during analysis and review

DRL targets empirical social science research -- economics, political science, sociology, public health -- where the standard deliverable is a LaTeX paper with regression tables, identification strategies, and robustness checks.

## Quick Start

### Install

```bash
# Clone and install
git clone <repo-url> && cd dark-research-lab
go install ./cmd/drl

# Or if distributed as a binary
brew install drl
```

### Initialize a New Research Project

```bash
drl setup
```

This scaffolds the project directory, installs templates, creates the decision log, and sets up the knowledge base.

### Customize for Your Field

```
/drl:flavor
```

The flavor command configures DRL's agents, knowledge base, and review criteria for your specific research domain. It adjusts the methodology reviewer's expectations, the writing conventions, and the default robustness checks based on your field's norms.

## The Research Pipeline

DRL structures research as a pipeline of phases, each with clear inputs and outputs. The end-to-end flow:

### Starting Point

You have a research question, access to data, and a target journal or audience in mind. DRL handles everything from question refinement to paper compilation.

### Step 1: Architect

```
/drl:architect
```

Decompose your research project into manageable epics. Each epic represents a self-contained piece of work (e.g., "estimate the baseline model," "run robustness checks," "write the introduction"). The architect assigns dependencies and sequencing.

### Step 2: Cook-It (The 5-Phase Cycle)

```
/drl:cook-it <epic>
```

Each epic passes through five phases:

**Phase 1 -- Specification**: Define the research question, hypotheses, and literature gap for this epic. Output: a research spec document that serves as the contract for the remaining phases.

**Phase 2 -- Planning**: Design the methodology, operationalize variables, select data sources, and define the analysis plan. Every methodological choice is logged to `docs/decisions/`. Output: an implementation plan.

**Phase 3 -- Work**: Execute the plan. Run regressions, generate tables and figures, draft paper sections. DRL agents handle both analysis (Python/Polars) and writing (LaTeX). Output: code, tables, figures, draft text.

**Phase 4 -- Review**: Multi-agent review of the work product. Separate agents evaluate methodology (is the identification credible?), statistical implementation (are standard errors correct?), and writing quality (does the prose follow conventions?). Output: review report with required changes.

**Phase 5 -- Synthesis**: Compile the reviewed outputs into the paper. Extract lessons learned and store them in the knowledge base for future work. Output: updated paper draft, captured lessons.

### Step 3: Iterate

Run multiple epics through the pipeline. Each builds on the outputs of previous epics. The architect tracks dependencies and ensures epics execute in the correct order.

### Step 4: Polish

The polish loop runs a multi-model advisory fleet over the near-final paper for final refinement -- checking consistency, flow, and presentation quality across all sections.

## Session Types

DRL supports different session types depending on what you need to accomplish:

### Literature Session

```
/drl:lit-review
```

Structured review of indexed papers. Produces a thematic literature summary, identifies gaps, and maps the contribution space. Use this early in the project to ground your research question.

### Specification Session

```
/drl:spec-dev
```

Interactive refinement of your research question, hypotheses, and identification strategy through Socratic dialogue. The spec agent challenges your assumptions and helps you articulate a precise, testable research design.

### Analysis Session

```
/drl:work
```

Selects work-analysis mode. Runs regressions, generates coefficient tables, produces figures, and stores outputs in `paper/outputs/`. Uses Python with Polars for data manipulation and statsmodels/linearmodels for estimation.

### Writing Session

```
/drl:work
```

Selects work-writing mode. Drafts paper sections in LaTeX following the conventions in the academic writing knowledge base. Produces output in `paper/sections/` that is compiled into `paper/main.tex`.

### Review Session

```
/drl:review
```

Multi-agent audit of both code and paper. The methodology reviewer checks identification, the statistical reviewer checks implementation, and the writing reviewer checks prose quality. Each produces a structured review with severity-classified findings.

### Decision Logging

```
/drl:decision
```

Log a methodological choice to `docs/decisions/`. Every non-trivial analytical decision (estimator choice, sample restriction, variable definition, robustness check selection) should be logged with its rationale and alternatives considered.

## Project Structure

After running `drl setup`, your project directory looks like this:

```
project/
  paper/                    # LaTeX paper
    main.tex                # Main paper file
    outputs/
      tables/               # Generated regression tables
      figures/              # Generated figures and plots
    sections/               # Individual section drafts
  src/                      # Python analysis code
    analysis/               # Regression scripts (econometrics, descriptive, robustness)
    data/                   # Data loading and cleaning
    visualization/          # Plots and figure generation
  data/
    input/                  # Raw data files (never modified)
    output/                 # Processed data and intermediate results
  literature/               # PDFs and reading notes
    notes/                  # Structured literature notes
  docs/
    decisions/              # Methodological decision log (ADRs)
      0000-template.md      # ADR template
    research/               # Knowledge base docs
  tests/                    # Test suite for analysis code
```

### Key Conventions

- **`data/input/` is read-only**: Raw data files are never modified. All transformations produce new files in `data/output/`.
- **`paper/outputs/` is machine-generated**: Tables and figures are produced by scripts in `src/`. Do not edit them manually.
- **`docs/decisions/` is append-only**: Decision records are never deleted or modified after creation.

## Key Principles

### Decision Logging Is Mandatory

Every methodological choice must be recorded. This is not bureaucracy -- it is the foundation of reproducible research. When a reviewer asks "why did you use fixed effects instead of random effects?" or "why did you winsorize at the 1st percentile?", the answer is in the decision log.

### Reproducibility Is Built In

All analysis code is tested. All data transformations are scripted. All tables and figures are generated from code, never manually assembled. The pipeline from raw data to final paper should be executable with a single command.

### Every Claim Needs Evidence

DRL agents are trained to challenge unsupported claims. If a paper section asserts that "X causes Y," there must be a regression table supporting it, an identification strategy justifying the causal language, and a robustness check demonstrating stability. Hedging language is required when identification is weak.

### Pre-Registration Mindset

Even when formal pre-registration is not required, DRL encourages specifying your analysis plan (Phase 2) before seeing the results (Phase 3). The specification phase locks in your hypotheses and methodology before the data is analyzed, reducing researcher degrees of freedom.

### The Knowledge Base Is a Living Resource

DRL ships with methodology reference docs covering econometrics, causal inference, robustness checks, identification strategies, and academic writing conventions. These docs are used by agents during analysis and review. You can extend the knowledge base with project-specific research using `/drl:lit-review` and `/drl:research`.
