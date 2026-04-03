---
name: Researcher
description: Deep domain research producing structured literature surveys and methodology references for working research agents
phase: spec-dev
---

# Researcher Skill

## Overview
Conduct deep domain research and produce a structured survey document for use by research agents. This skill spawns parallel research subagents to gather comprehensive academic literature, methodology conventions, and data source information, then synthesizes findings into a PhD-depth document stored in `docs/research/`.

## Methodology
1. Identify the research question, scope, field boundaries, and exclusions
2. Search memory with `drl search` for existing knowledge on the topic
3. Spawn parallel research subagents via Task tool:
   - **Literature specialist**: Uses WebSearch/WebFetch for academic papers, working papers, meta-analyses, and replication studies
   - **Methodology specialist**: Searches for field-specific conventions (estimation techniques, identification strategies, standard controls)
   - **Data source specialist**: Identifies available datasets, their coverage, access requirements, and known limitations
   - **Codebase explorer**: Uses `subagent_type: Explore` to find relevant existing analysis patterns in `src/analysis/`
   - **Docs scanner**: Reads `docs/` for prior research, ADRs, and methodology standards that inform the topic
4. Collect and deduplicate findings from all subagents
5. Synthesize into the research survey format (see Output Format below)
6. Store output at `docs/research/<topic-slug>.md` (kebab-case filename)
7. Report key findings back for upstream skill (spec-dev/plan) to act on

## Memory Integration
- Run `drl search` with topic keywords before starting research
- Check for existing research docs in `docs/research/` and `docs/drl/research/` that overlap
- After completion, key findings can be captured via `drl learn`

## Docs Integration
- Scan `docs/research/` and `docs/drl/research/` for prior survey documents on related topics
- Check `docs/decisions/` for ADRs that inform or constrain the research scope
- Reference existing project docs as primary sources where relevant

## Output Format

Every research document MUST follow this exact structure:

# [Topic Title]

*[Date]*

## Abstract
2-3 paragraph summary: what this survey covers, main approaches found in the literature, key methodological trade-offs.

## 1. Introduction
- Research question and motivation
- Scope: covered fields, time period, excluded topics
- Key definitions and operationalization of core concepts

## 2. Theoretical Foundations
Background theory relevant to the research question. Assume a reader trained in social science but not a domain specialist.

## 3. Taxonomy of Approaches
Classification of methodological approaches found in the literature. Present visually (table or tree) before diving into details. Organize by: identification strategy, estimation technique, or data type.

## 4. Literature Analysis
One subsection per approach:
### 4.x [Approach Name]
- **Theoretical basis**: Why this approach addresses the research question
- **Key papers**: Seminal and recent contributions with findings
- **Data requirements**: What data this approach needs, typical sources used
- **Identification strategy**: How causal claims are supported (if applicable)
- **Strengths and limitations**: Internal/external validity trade-offs

## 5. Data Landscape
Available datasets for this research question:
- Source, coverage, access method, known limitations
- Cross-reference with approaches that use each dataset

## 6. Comparative Synthesis
Cross-cutting trade-off table comparing approaches on: data requirements, identification strength, external validity, computational cost. No recommendations.

## 7. Open Problems and Gaps
Under-researched areas, methodological debates, replication failures, data limitations.

## 8. Conclusion
Synthesis of the landscape. No verdict -- the ADR process decides methodology.

## References
Full academic citations with DOIs/URLs where available.

## Practitioner Resources
Annotated tools, replication packages, datasets, and codebooks grouped by category.

## Common Pitfalls
- Shallow treatment: each approach needs theory, key papers, AND data requirements
- Missing taxonomy: always classify approaches before diving into analysis
- Recommendation bias: present trade-offs, never recommend (the `drl:decision` ADR process decides)
- Ignoring data limitations: explicitly state where data coverage is thin or access is restricted
- Not deduplicating subagent findings (leads to repetitive content)
- Skipping the comparative synthesis table
- Confusing correlation with identification: always note the identification strategy

## Quality Criteria
- PhD academic depth (reads like a published literature review)
- Multiple research subagents were deployed in parallel
- Memory was searched for existing knowledge
- Existing `docs/research/` was checked for overlap
- Every approach has: theory, key papers, data requirements, identification strategy, strengths/limitations
- Data landscape section present with source details
- Comparative synthesis table present with clear trade-offs
- Open problems honestly identified
- Full references with DOIs/URLs
- Practitioner resources annotated
- No recommendations -- landscape presentation only
