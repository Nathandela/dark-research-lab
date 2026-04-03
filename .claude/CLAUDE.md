# Project Instructions

## Dark Research Lab (DRL)

DRL is an autonomous research paper factory built on compound-agent. It targets social science research with methodological traceability.

### Decision Logging (Mandatory)

Every methodological decision MUST be logged to `docs/decisions/` using the ADR template (`docs/decisions/0000-template.md`). This includes:
- Statistical method choices (e.g., OLS vs. IV regression)
- Data source selections and exclusion criteria
- Variable operationalization decisions
- Robustness check design choices

Name files as `NNNN-slug.md` (e.g., `0001-use-polars-for-data.md`). Increment the number sequentially.

### Research-Spec Approval Gate

Before starting any analysis work phase, verify that the research specification epic has been approved:
- Check the parent epic's status in beads (`bd show <epic-id>`)
- The spec-dev phase must be complete (status field or notes confirm this)
- Do NOT begin data analysis or statistical work without an approved research specification

This is a soft advisory gate. If the spec is missing or unapproved, flag it and ask the user before proceeding.

### Namespace

All DRL-specific slash commands use the `/drl:*` namespace. Compound-agent commands remain under `/compound:*`.

### Output Format

DRL produces LaTeX papers. All generated tables and figures go to `paper/outputs/tables/` and `paper/outputs/figures/` respectively. The main paper file is `paper/main.tex`.

### Development Rules

- Python by default, using `uv` for package management
- Polars over pandas for data manipulation
- TDD workflow: tests first, then implementation
- Decision log every methodological choice

<!-- dark-research-lab:claude-ref:start -->
## Dark Research Lab
See AGENTS.md for lesson capture workflow.
<!-- dark-research-lab:claude-ref:end -->
