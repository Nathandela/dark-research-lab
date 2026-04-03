---
name: Research Spec
description: Define research question, hypotheses, methodology outline, and literature gap
phase: spec
---

# Research Spec Skill

## Overview

Refine a research question into a precise specification with testable hypotheses, a methodology outline, and a clear literature gap. This is the first phase of the DRL research pipeline -- nothing proceeds without an approved RQ and hypotheses.

## Input

- Beads epic ID: read epic description via `bd show <epic-id>`
- Research question: from epic description or via `AskUserQuestion`
- Literature context: search indexed papers via `drl knowledge`

## Methodology

### Step 1: Literature Landscape

1. Search memory: `drl search` for prior research decisions and constraints
2. Search knowledge: `drl knowledge "relevant terms"` for indexed literature
3. Spawn **literature-analyst** subagent (`.claude/agents/drl/literature-analyst.md`) to:
   - Survey indexed literature for the research domain
   - Identify gaps the RQ addresses
   - Extract methodological approaches from related studies
   - Flag conflicting findings

### Step 2: Research Question Refinement

1. Start with the working RQ from the epic description
2. Ask "why does this matter?" before "how do we test it?"
3. Build a **domain glossary**: key variables, constructs, operational definitions
4. Check that the RQ is:
   - Answerable with available or obtainable data
   - Specific enough to guide hypothesis formation
   - Connected to a clear literature gap

### Step 3: Hypothesis Generation

1. Derive testable hypotheses from the refined RQ
2. For each hypothesis, specify:
   - The expected relationship (direction, mechanism)
   - The theoretical basis (which literature supports this expectation)
   - The observable implication (what would confirm/disconfirm)
3. Distinguish between primary and secondary hypotheses

### Step 4: Methodology Outline

1. Sketch the analytical approach (not the full specification -- that is the plan phase)
2. Identify:
   - Key dependent and independent variables
   - Likely statistical methods (descriptive, regression, causal inference)
   - Data requirements (sources, sample, timeframe)
   - Potential threats to validity
3. This outline guides the research-plan phase but does not lock in methods

### Step 5: Literature Gap Statement

1. Synthesize literature-analyst findings into a gap statement:
   - What is known (prior findings)
   - What is not known (the gap)
   - How this research fills the gap (the contribution)
2. Ensure the gap is genuine, not manufactured by ignoring existing work

## Gate Criteria

**Gate: RQ + Hypotheses Approved**

Before proceeding to research-plan, verify ALL of:
- [ ] Research question is specific and answerable
- [ ] At least one testable hypothesis is articulated
- [ ] Literature gap is documented with evidence from indexed papers
- [ ] Methodology outline identifies key variables and likely methods
- [ ] Domain glossary defines core constructs

Use `AskUserQuestion` to confirm the research question and hypotheses with the researcher before proceeding.

## Memory Integration

- `drl search` before starting
- `drl knowledge` for literature context
- `drl learn` after corrections or discoveries

## Failure and Recovery

If the spec phase fails mid-execution:

1. **Literature search fails** (no indexed papers, `drl knowledge` returns nothing):
   - Verify `literature/pdfs/` has PDF files and run `drl index`
   - If no papers available, ask the researcher to provide initial literature
   - Do not proceed without at least one relevant source

2. **Human gate times out** (no response to `AskUserQuestion`):
   - Save the current draft spec to `docs/specs/` as a working draft
   - Update beads with progress notes: `bd update <id> --notes="Spec draft saved, awaiting human approval"`
   - The next cook-it invocation can resume from the draft

3. **RQ cannot be refined** (too broad, no data available):
   - Log the blocker as a beads note
   - Recommend running `/drl:architect` for structured decomposition
   - Do not force a spec when the RQ is not yet answerable

## Common Pitfalls

- Defining hypotheses before understanding the literature landscape
- RQ too broad to guide analysis ("What affects X?")
- Confusing the methodology outline with the full research plan
- Ignoring contradictory findings in the literature
- Not distinguishing primary from secondary hypotheses

## Quality Criteria

- [ ] Literature-analyst subagent was consulted
- [ ] RQ is refined from the initial working version
- [ ] Hypotheses are testable and theoretically grounded
- [ ] Literature gap is evidenced, not asserted
- [ ] Methodology outline is a sketch, not a locked-in plan
- [ ] Human approved RQ and hypotheses via gate
