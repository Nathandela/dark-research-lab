---
name: Work Writing
description: Draft and revise paper sections with proper citations and cross-references
---

# Work Writing Sub-Skill

## Overview

Write paper sections as LaTeX files. Every claim needs evidence -- either a citation or a reference to a generated table or figure. This sub-skill is invoked by the work router -- it does not run standalone.

## Agent Delegation

Deploy specialized writing agents:

- **Prose-drafter**: `.claude/skills/drl/agents/prose-drafter/SKILL.md` -- drafts section text
- **Section-writer**: `.claude/skills/drl/agents/section-writer/SKILL.md` -- structures sections with proper LaTeX formatting
- **Argumentation-builder**: `.claude/skills/drl/agents/argumentation-builder/SKILL.md` -- for argument structure and logical flow

## Methodology

### Step 1: Understand the Task

1. Read the task description: which section, what content, what arguments
2. Identify the target file: `paper/sections/{section}.tex`

### Step 2: Gather Evidence

1. Check `paper/outputs/tables/` and `paper/outputs/figures/` for available outputs to reference
2. Check `literature/notes/` and run `drl knowledge` for citation material
3. If literature context is insufficient, reference the lit-review skill (`/drl:lit-review`) for structured review capability

### Step 3: Draft the Section

1. Write LaTeX content to `paper/sections/{section}.tex`
2. Reference tables with `\input{outputs/tables/<file>}` and figures with `\includegraphics{outputs/figures/<file>}`
3. Interpret results in the context of hypotheses
4. Structure: opening claim, evidence, interpretation, transition

### Step 4: Verify References

1. Ensure all `\cite{}` keys exist in `paper/Ref.bib`
2. Ensure all `\ref{}` targets point to defined `\label{}` entries
3. Add missing BibTeX entries with complete metadata (author, title, year, journal, DOI)

### Step 5: Log Interpretive Decisions

Any interpretive choices (framing, emphasis, alternative explanations considered) must be logged to `docs/decisions/` using the ADR template. Use `/drl:decision` for guided logging.

## Verification Gate

- `paper/compile.sh` succeeds (or the manual triple-pass pdflatex chain)
- Zero "undefined reference" warnings in `paper/main.log`
- Zero "citation undefined" warnings in `paper/main.log`

## Scope

- All files in `paper/sections/`
- Bibliography: `paper/Ref.bib`
