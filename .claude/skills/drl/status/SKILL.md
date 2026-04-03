---
name: Status
description: Show research project progress, open tasks, blocked work, and pipeline health
---

# Project Status Skill

## Overview

Provide a comprehensive view of the research project's current state. This skill aggregates information from beads (task tracking), the decision log, the literature index, and the paper compilation status to give the researcher a clear picture of progress and actionable next steps.

## Step 1: Beads Task Overview

Query beads for the current project state:

1. **Summary statistics**: Run `bd stats` to see total tasks, completion rate, and phase distribution
2. **Open tasks**: Run `bd list --status=open` to see all incomplete work
3. **In-progress work**: Run `bd list --status=in_progress` to see what is actively being worked on
4. **Blocked tasks**: Run `bd blocked` to identify bottlenecks and dependencies that are stalling progress
5. **Recently completed**: Run `bd list --status=closed --limit=5` to show recent progress

If an epic ID is provided as an argument, scope all queries to that epic: `bd show <epic-id>` for details and `bd list --parent=<epic-id>` for its subtasks.

## Step 2: Research Phase Progress

Determine which research phase the project is in and how far along:

1. **Specification**: Is the research question defined? Are hypotheses articulated? Check for `docs/specs/` files.
2. **Planning**: Is the methodology designed? Check for analysis plan documents and beads subtasks.
3. **Work**: Are analyses running? Check for outputs in `paper/outputs/tables/` and `paper/outputs/figures/`.
4. **Review**: Has the review fleet run? Check for review-related beads tasks and their status.
5. **Synthesis**: Is the paper being compiled? Check `paper/main.tex` modification date and `paper/main.pdf` existence.

Report the current phase and percentage completion estimate based on closed vs. open subtasks.

## Step 3: Decision Log Summary

Summarize the ADR registry:

1. Count total decisions: `find docs/decisions -name "[0-9]*.md" ! -name "0000-template.md" 2>/dev/null | wc -l` (excluding the template)
2. List recent decisions (last 5 by file number)
3. Check for any decisions marked as "proposed" (not yet accepted)
4. Flag if no decisions exist yet (suggesting the project needs more methodological logging)

## Step 4: Literature Index Status

Assess the literature base:

1. Count PDFs in `literature/pdfs/`
2. Check if the literature index is populated (run `drl knowledge "test"` to verify indexing works)
3. Report whether the literature base meets the sufficiency threshold (at least 5 relevant papers)
4. Note if new papers have been added since the last index run

## Step 5: Paper Compilation Status

Check the state of the LaTeX paper:

1. Does `paper/main.tex` exist?
2. When was it last modified?
3. Does `paper/main.pdf` exist (has it been compiled)?
4. Count section files in `paper/sections/`
5. Count tables in `paper/outputs/tables/` and figures in `paper/outputs/figures/`
6. Check `paper/Ref.bib` for citation count

If the paper has been compiled, report whether the last compilation was clean (check `paper/main.log` for warnings).

## Step 6: Actionable Next Steps

Based on the gathered information, recommend concrete next steps:

1. **If no research question**: Recommend `/drl:onboard` or `/drl:architect`
2. **If no literature**: Recommend `/drl:lit-review` or adding papers to `literature/pdfs/`
3. **If specification incomplete**: Recommend continuing with `/drl:cook-it`
4. **If blocked tasks exist**: Identify the blocking dependency and suggest resolution
5. **If review findings are open**: List unresolved critical and major findings
6. **If paper not compiled**: Recommend `/drl:compile`
7. **If everything is done**: Recommend final review and submission preparation

## Output Format

Present the status as a structured report:

```
## Research Project Status

### Phase: [current phase] ([X]% complete)

### Task Summary
- Open: N | In Progress: N | Closed: N | Blocked: N

### Recent Activity
- [last 3-5 completed tasks or decisions]

### Decision Log
- Total decisions: N | Pending: N

### Literature
- Papers indexed: N | Sufficiency: [met/not met]

### Paper
- Sections: N/7 | Tables: N | Figures: N | Last compiled: [date or never]

### Next Steps
1. [most important action]
2. [second action]
3. [third action]
```

## Common Pitfalls

- Reporting only beads status without checking the actual file outputs
- Not checking for blocked tasks (which may silently stall the project)
- Forgetting to verify that the literature index is actually populated
- Not distinguishing between "task closed" and "task done well" (a closed task may have unresolved review findings)
- Reporting next steps without considering dependencies between them
