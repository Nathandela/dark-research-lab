---
name: Synthesis
description: Ensure cross-section coherence, clarify contribution, review decision log, extract lessons, and compile final LaTeX paper
phase: synthesis
---

# Synthesis Skill

## Overview

The final phase of the DRL research pipeline. Verify the paper tells a coherent story, the contribution is clear, the decision log is complete, and the LaTeX paper compiles cleanly with all references resolved. Extract lessons for future research cycles.

## Input

- Reviewed paper from the methodology-review phase
- Paper sections in `paper/sections/`
- Generated outputs in `paper/outputs/tables/` and `paper/outputs/figures/`
- Decision log in `docs/decisions/`
- Beads epic: `bd show <epic>` for original scope and hypotheses

## Methodology

### Step 1: Cross-Section Coherence

1. Read all paper sections in order:
   - `paper/sections/intro.tex`
   - `paper/sections/literature.tex`
   - `paper/sections/methodology.tex`
   - `paper/sections/data.tex`
   - `paper/sections/results.tex`
   - `paper/sections/robustness.tex`
   - `paper/sections/conclusion.tex`
2. Verify the narrative arc:
   - Introduction states the RQ and previews findings
   - Literature review motivates the RQ and methodology
   - Methodology section matches the actual analysis performed
   - Data section describes exactly what the analysis used
   - Results address every hypothesis
   - Robustness section strengthens (or qualifies) the main findings
   - Conclusion does not overclaim beyond the evidence
3. Check that the abstract in `paper/main.tex` accurately summarizes the full paper

### Step 2: Contribution Clarity

1. Verify the paper clearly states what is new:
   - What gap does this fill?
   - How do findings advance understanding?
   - What are the practical or theoretical implications?
2. Check that the contribution claim is proportionate to the evidence
3. Ensure limitations are honestly acknowledged

### Step 3: Decision Log Review

1. Read all ADRs in `docs/decisions/`
2. Verify completeness:
   - Every methodological choice in the paper has a corresponding ADR
   - ADR statuses are current (proposed/accepted/deprecated)
   - Alternatives considered are documented
3. Flag any undocumented decisions and create ADRs for them

### Step 4: Final LaTeX Compilation

**This is a hard gate (H4 mitigation).**

1. Run the LaTeX compile script:
   ```bash
   bash paper/compile.sh
   ```
2. Verify:
   - `paper/main.pdf` is generated without errors
   - No undefined references (ref or cite warnings)
   - All tables and figures render correctly
   - Bibliography compiles without BibTeX warnings
   - All input sections files exist and are included
3. If compilation fails:
   - Fix LaTeX errors (missing packages, syntax issues)
   - Resolve undefined references
   - Re-run compilation until clean

### Step 5: Lesson Extraction

1. Review the full research cycle:
   - What worked well in the methodology?
   - What required unexpected changes from the plan?
   - Which robustness checks were most informative?
   - What would you do differently next time?
2. Capture lessons via `drl learn` for each significant insight
3. Check for patterns that apply to future research projects

### Step 6: Final Verification

1. Run the test suite: `uv run python -m pytest`
2. Verify all beads tasks are closed: `bd list --status=open` should only show the epic itself
3. Verify the reproducibility package:
   - Analysis code in `src/` is complete
   - Data pipeline is documented
   - Dependencies pinned in `uv.lock`

## Gate Criteria

**Gate 5: Paper Compiles + All Refs Resolve**

Before closing the epic, verify ALL of:

| Criterion | Verification |
|-----------|-------------|
| Paper compiles without errors | `bash paper/compile.sh` exits 0 |
| No undefined ref/cite references | `grep -ci "undefined" paper/main.log` returns 0 |
| Bibliography resolves all citations | `grep -ci "warning" paper/main.blg` returns 0 |
| Cross-section coherence verified | Read all sections end-to-end |
| Contribution clearly stated | Review intro and conclusion sections |
| Decision log complete | `ls docs/decisions/` matches decisions in paper |
| Lessons extracted | `drl learn` called for each insight |
| Tests pass | `uv run python -m pytest` |
| All sub-tasks closed | `bd list --status=open` shows only the epic |


## Handoff Checklist

| Output | Location | Format | Next Phase Retrieval |
|--------|----------|--------|---------------------|
| Compiled paper | `paper/main.pdf` | PDF with all references resolved | Final deliverable -- no next phase |
| Complete decision log | `docs/decisions/NNNN-*.md` | All ADRs with accepted/deprecated status | Archived for future research cycles |
| Lessons captured | `drl learn` entries | Memory system entries | Future cook-it cycles retrieve via `drl search` |
| Closed epic | Beads (`bd show <epic-id>`) | Epic status = closed | Pipeline complete |

## Memory Integration

- `drl search` for patterns from prior synthesis cycles
- `drl learn` for each lesson extracted
- Update or deprecate stale ADRs in `docs/decisions/`

## Failure and Recovery

If the synthesis phase fails mid-execution:

1. **LaTeX compilation fails**:
   - Read the compile output for specific errors (missing packages, syntax, undefined refs)
   - Fix one error at a time and re-compile -- LaTeX errors cascade
   - Check that all `\input{sections/*.tex}` files exist

2. **Undefined references** (`\ref` or `\cite` warnings):
   - For `\cite`: verify the key exists in `paper/Ref.bib` and run BibTeX
   - For `\ref`: verify the label exists in the referenced section file
   - Re-compile after each fix

3. **Decision log incomplete** (undocumented choices found):
   - Create the missing ADRs before closing the epic
   - Do not close the epic with undocumented methodological decisions

4. **Cross-section incoherence** (narrative arc broken):
   - Identify the specific sections that conflict
   - Fix the downstream section to match the upstream one (not vice versa)
   - Re-read end-to-end after fixes

## Common Pitfalls

- Not reading the paper end-to-end (reviewing sections in isolation)
- Conclusion overclaiming beyond the evidence
- Missing undocumented methodological decisions
- Skipping the LaTeX compile gate ("it compiled last time")
- Not extracting lessons (losing the compounding benefit)
- Leaving orphan references or unreferenced tables/figures

## Quality Criteria

- [ ] All paper sections read end-to-end for coherence
- [ ] Contribution statement is clear and proportionate
- [ ] Decision log is complete with no undocumented choices
- [ ] LaTeX compiles cleanly (hard gate)
- [ ] All references resolve (no warnings)
- [ ] Lessons captured for future research cycles
- [ ] Reproducibility package is complete
- [ ] Epic closure criteria met
