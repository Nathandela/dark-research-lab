---
name: Research Architect
description: Decompose a research question into cook-it-ready epic beads with methodology specifications
phase: architect
---

# Research Architect Skill

## Overview

Take a research question and decompose it into naturally-scoped research epic beads that the infinity loop can process via cook-it. Each output epic represents a coherent unit of research work (a paper section, an analysis pipeline, a robustness battery, etc.).

This skill organizes work around research domain boundaries: literature review, data collection, analysis, robustness, and synthesis.

## Input

- Beads epic ID: read epic description as input
- Research question: provided directly or via `AskUserQuestion`
- Literature context: search indexed papers via `drl knowledge`

## Phase 1: Socratic (Research Question Refinement)

**Goal**: Understand the research domain and refine the question before decomposing.

1. Search memory: `drl search` for past research decisions, constraints, methodology patterns
2. Search knowledge: `drl knowledge "relevant terms"` for indexed literature and project docs
3. **Literature sufficiency gate** (see below)
4. Ask "why does this matter?" before "how do we test it?" -- understand the contribution
5. Build a **domain glossary**: key variables, constructs, and their operational definitions
6. Produce a **research mindmap** (Mermaid `mindmap`) exposing:
   - Central research question
   - Key theoretical constructs
   - Potential data sources
   - Methodological approaches
   - Expected contributions
7. **Hypothesis generation**: Help the researcher articulate testable hypotheses from the research question
8. Use `AskUserQuestion` to clarify scope, field conventions, and methodological preferences

### Literature Sufficiency Gate

After steps 1-2, evaluate whether the literature base is adequate:

1. **Collect results**: Gather hits from `drl knowledge` and any PDFs in `literature/pdfs/`
2. **Evaluate coverage**: Score each result for relevance to the research question
3. **Apply threshold**: If fewer than 3 relevant sources cover the research question's domain:
   - **Insufficient**: Recommend adding more literature to `literature/pdfs/` and re-indexing with `drl index`. Use `AskUserQuestion` to confirm.
   - **Sufficient**: Note the evidence and proceed.
4. **Time budget**: Literature review is capped at 3 search rounds.

**Gate 1**: Use `AskUserQuestion` to confirm the research question, hypotheses, and scope.

## Phase 2: Research Specification

**Goal**: Produce a research-level specification.

1. Write **research EARS requirements** adapted for social science:
   - Ubiquitous: "The analysis SHALL control for X"
   - Event: "WHEN data shows outliers, the pipeline SHALL flag them"
   - State: "WHILE running robustness checks, the system SHALL log each specification"
   - Unwanted: "IF a key variable has >20% missing data, THEN the analysis SHALL not proceed without imputation justification"
2. Produce **research design diagrams**:
   - Causal diagram (DAG) showing hypothesized relationships
   - Analysis pipeline flowchart (data -> cleaning -> analysis -> robustness -> output)
   - Variable operationalization table
3. Write the spec to `docs/specs/<research-topic>.md`
4. Create a **meta-epic bead** for the research project

**Gate 2**: Use `AskUserQuestion` to get human approval of the research specification.

## Phase 3: Decompose (Research Subagent Convoy)

**Goal**: Break the research project into naturally-scoped epics.

Spawn **6 parallel subagents** via the Agent tool. Each subagent is an inline role description passed as the Agent tool prompt -- these are NOT references to pre-defined agent files in `.claude/agents/drl/`. Write a focused prompt for each role describing the task and expected output.

**Why inline prompts here?** These are temporary decomposition roles used only during architecture. Unlike the methodology-review phase -- which spawns persistent, reusable agents defined in `.claude/agents/drl/` (e.g., `methodology-reviewer.md`, `robustness-checker.md`) -- these roles are single-use analytical lenses that do not need persistent definitions. If a decomposition role proves repeatedly useful, promote it to a dedicated agent file.

1. **Literature mapper**: Survey the indexed literature to identify:
   - Key prior studies and their methodological approaches
   - Theoretical frameworks that inform the hypotheses
   - Gaps that the research question addresses
   - Conflicting findings that need reconciliation

2. **Methodology analyst**: Evaluate and recommend:
   - Appropriate statistical methods for the research question
   - Identification strategy for causal claims (if applicable)
   - Required sample size and statistical power
   - Assumptions and their testability

3. **Data requirements analyst**: Specify:
   - Required variables and their sources
   - Data quality criteria (completeness, validity, reliability)
   - Sample selection and exclusion criteria
   - Data cleaning and transformation pipeline

4. **Scope sizer**: Assess each proposed epic for:
   - "One cook-it cycle" feasibility
   - Cognitive load (7+/-2 concepts per epic)
   - Dependencies on other epics
   - Risk of scope creep

5. **Traceability designer**: Map:
   - Hypothesis -> analysis -> output -> paper section chains
   - Variable -> data source -> cleaning step -> model input chains
   - Decision points that require ADR logging
   - Which agent role handles each step

6. **Risk analyst**: Identify:
   - Data availability and quality risks
   - Methodological risks (endogeneity, selection bias, measurement error)
   - Scope risks (analysis may reveal need for additional data or methods)
   - Reproducibility risks (environment, dependency, randomness)

**Synthesis**: Merge subagent findings into a proposed epic structure. For each epic:
- Title and scope boundaries (what is in, what is out)
- Relevant EARS subset from the research spec
- Interface contracts: data format, variable naming, output format
- Assumptions that must hold
- Which DRL agent roles are involved
- Decision points requiring ADR logging

**Gate 3**: Use `AskUserQuestion` to get human approval of the epic structure.

## Phase 4: Materialize

**Goal**: Create the actual beads.

1. Create epic beads via `bd create --title="..." --type=epic --priority=<N>` for each approved epic
2. Store scope, EARS subset, interface contracts, and assumptions in each epic description
3. Wire dependencies via `bd dep add` for all relationships
4. Store processing order as notes on the meta-epic
5. **Create Integration Verification epic**: Validates cross-epic interfaces (shared data formats, variable naming consistency, output compatibility)
6. Capture lessons via `drl learn`

### Standard Research Epic Structure

A typical decomposition produces these epics (adjust based on the research question):

1. **Literature Review**: Survey and synthesize prior work (literature-analyst agent)
2. **Data Pipeline**: Collect, clean, and validate data (analyst agent)
3. **Main Analysis**: Run primary statistical models (analyst + methodology-reviewer agents)
4. **Robustness Battery**: Alternative specifications, sensitivity checks (robustness-checker agent)
5. **Paper Synthesis**: Write and compile the paper (writing-quality-reviewer + citation-checker agents)
6. **Integration Verification**: Cross-epic consistency checks (coherence-reviewer + reproducibility-verifier agents)


### Epic Description Format

Each epic created in Phase 4 MUST use this structured format in its beads description. This ensures consistent handoff to cook-it:

```markdown
## Scope
What is in scope and what is explicitly out of scope for this epic.

## EARS
Research EARS requirements (ubiquitous, event, state, unwanted) from the spec.

## Contracts
Interface contracts: data format, variable naming, output format, file paths.
How this epic's outputs connect to other epics' inputs.

## Assumptions
Assumptions that must hold for this epic to succeed.
Data availability, methodological feasibility, sample size adequacy.

## Roles
Which DRL agent roles are involved (analyst, methodology-reviewer, etc.).

## Decisions
Decision points that require ADR logging during execution.
Known methodological choices that will need to be made.
```

This format allows cook-it to parse the epic description and route information to the correct phase.

## Advisory Fleet Integration

WHERE external model CLIs are available (gemini, codex), include them in review:
1. Detect available advisor CLIs with health-check Bash calls
2. Assign review lenses:
   - **Methodological Rigor**: Are the statistical methods appropriate?
   - **Literature Coverage**: Are key papers missing?
   - **Logical Coherence**: Does the argument flow hold?
   - **Simplicity**: Is the research design unnecessarily complex?
3. Synthesize advisory feedback before presenting to the human

If no advisor CLIs are available, skip. The advisory fleet is non-blocking.

## Memory Integration

- `drl search` before starting each phase
- `drl knowledge` for indexed literature and project docs
- `drl learn` after corrections or discoveries

## Common Pitfalls

- Jumping to methodology without understanding the research question (skip Socratic)
- Proposing methods that exceed the data's capacity to support
- Not checking the indexed literature for contradictory findings
- Missing the hypothesis -> analysis -> output -> section traceability chain
- Creating epics that are too fine-grained (a single regression is not an epic)
- Not logging methodological decisions to `docs/decisions/` (use ADR template at `docs/decisions/0000-template.md` or `/drl:decision`)
- Ignoring data quality and availability risks
- Treating the research design as fixed before the literature review
- Not wiring epic dependencies (analysis before data pipeline)

## Quality Criteria

- [ ] Socratic phase completed with research question refinement and hypothesis generation
- [ ] Literature sufficiency gate evaluated
- [ ] Research EARS requirements cover all hypotheses and methodological constraints
- [ ] Research design diagrams produced (causal DAG, pipeline flowchart, variable table)
- [ ] Spec written to `docs/specs/`
- [ ] 6-subagent convoy executed (literature, methodology, data, scope, traceability, risk)
- [ ] Each epic has scope, EARS subset, interface contracts, and assumptions
- [ ] Dependencies wired via `bd dep add`
- [ ] Integration Verification epic created
- [ ] Advisory fleet consulted (or skipped with documented reason)
- [ ] 3 human gates passed via `AskUserQuestion`
- [ ] Memory searched at each phase
- [ ] All methodological decisions logged to `docs/decisions/`
