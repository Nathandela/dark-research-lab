---
name: Literature Review
description: Conduct a structured literature review using indexed papers and the literature-analyst agent
---

# Literature Review Skill

## Overview

Conduct a structured, systematic literature review for a research topic. This skill searches indexed papers, builds a citation network, identifies gaps, and produces a literature review section ready for the paper.

## Input

- Research topic or question (from arguments or via `AskUserQuestion`)
- Existing literature in `literature/pdfs/`
- Indexed knowledge base (searchable via `drl knowledge`)

## Step 1: Search Indexed Literature

1. Run `drl knowledge "<topic keywords>"` with multiple search queries:
   - Broad topic terms
   - Specific construct names
   - Key author names (if known)
   - Methodological terms relevant to the topic
2. Collect and deduplicate results
3. Score each result for relevance to the research question (high, medium, low)
4. Record the search queries used for reproducibility

## Step 2: Add New Papers

If the indexed literature is insufficient (fewer than 5 highly relevant sources):

1. Use `AskUserQuestion` to ask the researcher for additional papers
2. Instruct them to drop PDFs into `literature/pdfs/`
3. Run `drl index` to process and index the new papers
4. Re-run the search queries from Step 1
5. Repeat until the literature base is adequate

### Literature Sufficiency Criteria

- At least 3-5 papers directly address the research question
- At least 2-3 papers cover the proposed methodology
- At least 1-2 papers address the same data source or context
- Key seminal works in the field are present

## Step 3: Build Citation Network

For the relevant papers identified:

1. **Map relationships**: Which papers cite each other? Which build on prior work?
2. **Identify streams**: Group papers into thematic streams (theoretical, empirical, methodological)
3. **Find consensus**: Where do findings agree across studies?
4. **Find disagreement**: Where do findings conflict? What explains the divergence?
5. **Trace evolution**: How has understanding of the topic evolved over time?

## Step 4: Spawn Literature-Analyst Agent

Spawn the literature-analyst agent (`.claude/agents/drl/literature-analyst.md`) to:

1. Synthesize findings across the collected papers
2. Identify the specific gap this research addresses
3. Extract methodological approaches used in prior work
4. Note limitations of existing studies that this research overcomes
5. Produce a structured summary organized by theme, not by paper

## Step 5: Produce the Literature Review Section

Write the literature review for `paper/sections/literature.tex`:

1. **Opening**: Establish the broader topic and its importance
2. **Thematic synthesis**: Organize by research streams, not paper-by-paper summaries
3. **Methodological landscape**: What methods have been used and what are their limitations
4. **Gap identification**: State clearly what is not yet known
5. **Bridge to this research**: How the current study addresses the gap
6. **Citations**: Ensure every claim is cited and every citation has a BibTeX entry in `paper/Ref.bib`

## Step 6: Update BibTeX

1. Verify all cited works have entries in `paper/Ref.bib`
2. Add missing BibTeX entries with complete metadata (authors, year, title, journal, volume, pages, DOI)
3. Check for duplicate or inconsistent entries
4. Ensure citation keys follow a consistent format

## Gate Criteria

Before concluding the literature review, verify:
- [ ] At least 5 relevant papers identified and synthesized
- [ ] Citation network mapped (relationships between papers documented)
- [ ] Literature gap clearly stated with supporting evidence
- [ ] Literature review section written for `paper/sections/literature.tex`
- [ ] All citations have BibTeX entries in `paper/Ref.bib`
- [ ] Search queries recorded for reproducibility

## Memory Integration

- `drl search` before starting for prior literature review findings
- `drl knowledge` for indexed paper search
- `drl learn` after identifying key findings or gaps

## Common Pitfalls

- Organizing the review paper-by-paper instead of by theme
- Not searching with enough diverse query terms
- Accepting the first few results without assessing sufficiency
- Missing seminal or foundational works in the field
- Not updating BibTeX entries when adding new citations
- Treating the literature review as complete without checking for contradictory findings
- Manufacturing a gap by ignoring papers that already address the question
