---
name: Research Codebase Setup
description: Audit and set up a research codebase for autonomous research pipelines (Python analysis, LaTeX paper, data directories, decision logging)
phase: work
---

# Research Codebase Setup Skill

## Overview

Assess and improve a research codebase's readiness for autonomous research pipelines. Based on a research infrastructure framework organized across 3 pillars: traceability, reproducibility, and navigability.

This skill operates in two modes:
- **Mode: audit** -- Score the codebase against all 12 principles, produce a report with evidence and prioritized actions
- **Mode: setup** -- Run audit first, then incrementally fill gaps with real content generated from codebase analysis

Mode is set by the calling command (`/drl:agentic-audit` or `/drl:agentic-setup`). The command wrapper tells you which mode to run -- do not parse `$ARGUMENTS` for mode detection.

## Stack Detection

Before auditing, detect the research project structure:
1. Look for `pyproject.toml` or `setup.py` (Python analysis code)
2. Check for `paper/main.tex` (LaTeX paper structure)
3. Identify data directories (`src/data/`, `data/raw/`, `data/processed/`)
4. Check for decision registry (`docs/decisions/`)
5. Look for analysis pipeline entry points (`src/analysis/`)
6. Detect test infrastructure (`tests/`, `pytest.ini`, `conftest.py`)
7. Store detected structure for use in principle checks

## Audit Methodology

### Scoring Rubric
Each principle is scored:
- **0 (Absent)**: No evidence of this principle in the codebase
- **1 (Partial)**: Some evidence but incomplete or inconsistent
- **2 (Present)**: Clear, consistent implementation

### The 12 Principles

#### Pillar I: Research Traceability -- max 8 points

**P1. Repository is the single source of truth**
Check: All context a research agent needs lives in version control
Evidence: Look for `docs/`, analysis scripts, data dictionaries, methodology notes
Score 0: No documentation beyond boilerplate README
Score 1: README exists but key methodology context lives elsewhere
Score 2: Comprehensive `docs/`, data dictionaries, and methodology notes all in-repo

**P2. Trace methodological decisions**
Check: Every statistical/methodological choice has recorded rationale
Evidence: Look for `docs/decisions/` with ADR-style records
Score 0: No decision records
Score 1: Some decisions documented but inconsistent format
Score 2: `docs/decisions/` directory with structured ADR records for each methodological choice

**P3. Document data provenance**
Check: Data sources, transformations, and exclusion criteria are recorded
Evidence: Data dictionaries, ETL documentation, variable codebooks
Score 0: No data provenance documentation
Score 1: Scattered notes but no systematic approach
Score 2: Structured data dictionaries and transformation logs

**P4. Knowledge is versioned infrastructure**
Check: Literature notes, variable definitions, and methodology references are versioned alongside code
Evidence: `docs/research/`, literature index, variable operationalization docs
Score 0: Research knowledge lives outside version control
Score 1: Some docs in repo but key references are external
Score 2: Literature index, methodology references, and research knowledge all versioned

#### Pillar II: Reproducibility -- max 8 points

**P5. Tests are specification**
Check: Analysis pipeline has tests that define expected behavior
Evidence: `tests/` directory, pytest configuration, data validation tests
Score 0: No tests
Score 1: Tests exist but incomplete (no data validation, no pipeline tests)
Score 2: Comprehensive test suite covering data validation, transformations, and statistical outputs

**P6. Environment is locked**
Check: Python dependencies, random seeds, and runtime config are pinned
Evidence: `pyproject.toml` with pinned deps, seed configuration, environment reproducibility
Score 0: No dependency pinning or seed management
Score 1: Dependencies listed but not pinned; seeds not systematic
Score 2: Locked dependencies via `uv.lock`, documented seeds, reproducible environment

**P7. Pipeline outputs are verifiable**
Check: Tables, figures, and statistics can be regenerated from source data
Evidence: End-to-end pipeline scripts, output validation, Makefile or equivalent
Score 0: Manual copy-paste of results into paper
Score 1: Some scripts but gaps in the pipeline
Score 2: Full pipeline from raw data to LaTeX outputs with verification

**P8. Fight entropy continuously**
Check: Automated formatting, dependency updates, output consistency checks
Evidence: Pre-commit hooks, CI checks, output regression tests
Score 0: No automated maintenance
Score 1: Basic formatting but no pipeline monitoring
Score 2: Automated formatting + dependency management + output consistency checks

#### Pillar III: Navigable Structure -- max 8 points

**P9. Map, not manual**
Check: Entry point document provides a navigable map of the research project
Evidence: AGENTS.md, CLAUDE.md, or structured README with project map
Score 0: No agent-facing entry point document
Score 1: README exists but not optimized for research agents
Score 2: Dedicated AGENTS.md/CLAUDE.md with analysis commands, directory structure, conventions

**P10. Modular analysis pipeline**
Check: Single responsibility per module, clear boundaries between data/analysis/output
Evidence: Separation of `src/data/`, `src/analysis/`, `paper/`
Score 0: Monolithic scripts mixing data loading, analysis, and output
Score 1: Some separation but large files remain
Score 2: Clean separation with clear APIs between data, analysis, and paper generation

**P11. Paper structure follows conventions**
Check: LaTeX paper follows standard academic structure with proper sectioning
Evidence: `paper/sections/`, `paper/outputs/tables/`, `paper/outputs/figures/`
Score 0: No LaTeX structure or single monolithic file
Score 1: LaTeX exists but outputs not organized
Score 2: Proper `paper/` structure with separated sections, tables, and figures directories

**P12. Explicit variable operationalization**
Check: Variables are explicitly defined with measurement, source, and transformation documented
Evidence: Variable codebook, type annotations in analysis code, documented transformations
Score 0: No variable documentation, implicit transformations
Score 1: Some variables documented but gaps
Score 2: Complete variable codebook with measurement definitions and transformation logic

### Audit Execution Steps

1. Run `drl search "research codebase setup"` for relevant lessons
2. Detect project structure (see Stack Detection above)
3. Use Glob and Grep to check for evidence of each principle:
   - Glob for: `docs/**`, `tests/**`, `test_*.py`, `src/analysis/**`, `paper/**`, `AGENTS.md`, `CLAUDE.md`
   - Grep for: type annotations, seed configuration, data validation patterns
   - Read key files: README, `pyproject.toml`, sample analysis scripts
4. Score each principle (0-2) with specific evidence
5. Aggregate scores by pillar and compute total out of 24
6. Generate prioritized actions (score-0 first, then score-1)
7. Present report to user

### Report Format

Present as markdown tables per pillar:

Pillar I: Research Traceability -- X/8
| # | Principle | Score | Evidence |
|---|-----------|-------|----------|
| P1 | Repository is the single source of truth | 0/1/2 | finding |
...repeat for all pillars with separator rows...

**Overall Score: X/24**

### Priority Actions
1. [Score-0 items first, most impactful]
2. ...

After presenting, use `AskUserQuestion`: "Create a beads epic with issues for improvements?"
If yes, create epic via `bd create` and individual issues.

## Setup Methodology

### Prerequisites
Run the full audit first. Setup only addresses gaps found by the audit.

### Setup Execution Steps

1. Present audit findings summary
2. For each principle scored 0 or 1, propose a concrete action:

**P1/P4 gaps**: Create `docs/` skeleton with `docs/research/`, `docs/decisions/`, literature index
**P2 gaps**: Create ADR template at `docs/decisions/0000-template.md` and first decision record
**P3 gaps**: Create data dictionary template and provenance documentation structure
**P5 gaps**: Set up pytest with `conftest.py`, data validation fixtures, pipeline test stubs
**P6 gaps**: Configure `pyproject.toml` with pinned deps, add seed management utilities
**P7 gaps**: Create Makefile or pipeline script linking raw data to LaTeX outputs
**P8 gaps**: Set up pre-commit hooks (ruff, black), output regression checks
**P9 gaps**: Generate AGENTS.md by analyzing actual codebase structure and analysis commands
**P10 gaps**: Restructure into `src/data/`, `src/analysis/`, `paper/` with clear module boundaries
**P11 gaps**: Create `paper/sections/`, `paper/outputs/tables/`, `paper/outputs/figures/` structure
**P12 gaps**: Create variable codebook template, add type hints to analysis modules

3. Before each action, use `AskUserQuestion`: "Create [file]? Preview: [content]"
4. Only create/modify files the user approves
5. Never overwrite existing files without explicit approval

### Setup Completion Gate
After all approved actions are applied, verify:
- List all files created/modified during setup
- Run `uv run python -m pytest` if test infrastructure was created
- Confirm no existing files were overwritten without approval
- Present summary: principles addressed, files created, remaining gaps

## Memory Integration

- Before analysis: `drl search "research codebase setup"` for relevant lessons
- After completing: offer `drl learn` to capture insights

## Common Pitfalls

- Scoring too generously without specific evidence for score 2
- Generating template content instead of analyzing the actual research codebase
- Overwriting existing analysis scripts or data files without asking
- Creating too many files at once instead of prioritizing by research impact
- Forgetting to check for existing decision records before creating new ones
- Not detecting the analysis pipeline structure before generating content

## Quality Criteria

- All 12 principles assessed with specific evidence
- Scores justified with findings from the actual codebase
- Pillar totals and overall score calculated correctly
- Actions prioritized (score-0 before score-1)
- Research project structure detected and checks adapted accordingly
- User consulted via AskUserQuestion at key decisions
- Memory searched before analysis
- Setup mode ran audit first
- No files overwritten without approval
- Generated content based on actual codebase analysis, not templates
