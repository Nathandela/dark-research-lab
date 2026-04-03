---
name: Onboard
description: Interactive onboarding wizard that guides new researchers through the Dark Research Lab framework
---

# Onboarding Wizard

## Overview

Guide a new researcher through the Dark Research Lab (DRL) framework -- an autonomous research paper factory for social science. This wizard walks through the entire setup process, from understanding the framework to launching a first research project.

## Step 1: Explain the DRL Framework

Introduce the researcher to the DRL research pipeline:

1. **What DRL is**: An autonomous research paper factory that takes a research question and produces a LaTeX paper with full methodological traceability. Every statistical choice, data decision, and variable operationalization is logged.
2. **How it works**: DRL orchestrates research through five phases -- specification (defining the question and hypotheses), planning (designing the methodology), work (executing the analysis), review (auditing methodology and results), and synthesis (compiling the final paper).
3. **Key concepts**:
   - **Beads**: Task tracking system for organizing research work into epics and subtasks
   - **ADR registry**: Decision log at `docs/decisions/` that records every methodological choice with rationale
   - **Literature index**: Indexed papers in `literature/pdfs/` that inform the research
   - **LaTeX output**: Final paper compiled from `paper/main.tex` with tables and figures

## Step 2: Ask About the Research Question

Use `AskUserQuestion` to understand the researcher's goals:

1. What is the broad research topic or domain?
2. Do they have a specific research question, or do they need help formulating one?
3. What field are they working in (economics, sociology, political science, psychology, etc.)?
4. Is this exploratory research or hypothesis-driven?
5. What is the intended contribution (theoretical, empirical, methodological)?

Record the answers -- they feed into flavor configuration and the architect phase.

## Step 3: Ask About Data

Use `AskUserQuestion` to understand the data situation:

1. Do they already have data, or do they need to collect or source it?
2. What format is the data in (CSV, database, API, survey, etc.)?
3. What is the unit of observation (individuals, firms, countries, time periods)?
4. Approximate sample size and time coverage?
5. Any known data quality concerns (missing values, measurement issues)?

If no data exists yet, note this -- the architect phase will include a data collection epic.

## Step 4: Suggest Flavor Configuration

Explain that DRL skills can be customized for field-specific conventions:

1. Describe what `/drl:flavor` does -- it adapts the skill files to match field conventions, journal requirements, and citation styles
2. Ask if they want to configure flavor now or later
3. If now, recommend running `/drl:flavor` with their field and target journal
4. Common configurations: APA for psychology, Chicago for sociology, journal-specific for economics

## Step 5: Guide Literature Setup

Explain how to populate the literature base:

1. **Adding papers**: Drop PDF files into `literature/pdfs/`
2. **Indexing**: Run `drl index` to process and index the papers for search
3. **Searching**: Use `drl knowledge "search terms"` to query indexed literature
4. **Minimum threshold**: Recommend at least 5-10 core papers before starting the architect phase
5. **BibTeX**: Ensure `paper/Ref.bib` contains entries for all cited works

## Step 6: Suggest Next Steps

Recommend the natural progression:

1. **If literature is ready**: Run `/drl:architect` to decompose the research question into actionable epics
2. **If literature needs work**: Run `/drl:lit-review` to conduct a structured review first
3. **If the question needs refinement**: The architect phase includes a Socratic refinement step

Explain the full pipeline: `/drl:architect` -> `/drl:cook-it` -> `/drl:compile`

## Step 7: Explain Monitoring

Show how to track progress throughout the research:

1. **`/drl:status`**: Shows overall progress, open tasks, blocked work, and what to do next
2. **Beads commands**: `bd list` for tasks, `bd stats` for summary, `bd blocked` for bottlenecks
3. **Decision log**: Browse `docs/decisions/` to see all recorded methodological choices
4. **Paper output**: Check `paper/outputs/tables/` and `paper/outputs/figures/` for generated results

## Gate Criteria

Before concluding onboarding, verify:
- [ ] Researcher understands the five research phases
- [ ] Research question (even if preliminary) is captured
- [ ] Data situation is assessed (have data, need data, or data source identified)
- [ ] Literature directory `literature/pdfs/` location is known
- [ ] Next step is identified (flavor, lit-review, or architect)

## Common Pitfalls

- Skipping the literature setup and jumping straight to analysis
- Not configuring flavor for the target field and journal
- Starting analysis without a clear research question
- Forgetting that every methodological choice needs an ADR entry
