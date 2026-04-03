---
name: Methodology Review
description: Audit statistical validity, logical consistency, citation accuracy, reproducibility, and writing quality
phase: review
---

# Methodology Review Skill

## Overview

Conduct a comprehensive review of the completed research work. Six specialized reviewers check different dimensions of quality: statistical methodology, robustness assessment, logical coherence, citation integrity, reproducibility, and writing standards. All checks must pass before the paper proceeds to synthesis.

**Note**: The literature-analyst agent is NOT spawned during this phase. Literature analysis occurs during the spec phase (research-spec) and the standalone lit-review skill. This phase focuses on auditing the completed work using the six dedicated reviewer agents listed below.

## Input

- Completed analysis outputs from the work phase
- Paper sections with results interpretation
- ADR decision log in `docs/decisions/`
- Beads epic: `bd show <epic>` for EARS requirements

## Methodology

### Step 1: Pre-Review Baseline

1. Run the test suite: `uv run python -m pytest`
2. Verify all work tasks are closed: `bd list --status=in_progress` must be empty
3. Read the epic description for EARS requirements and acceptance criteria
4. Search memory: `drl search` for known issues and past review findings

### Step 2: Spawn Review Fleet

Spawn **6 specialized reviewer subagents** in parallel:

#### 2a. Statistical Validity -- methodology-reviewer

Spawn `.claude/agents/drl/methodology-reviewer.md`:
- Evaluate identification strategy and causal claims
- Check model assumptions (linearity, homoscedasticity, independence)
- Assess variable selection for omitted variable bias
- Verify correct standard error clustering and multiple testing corrections
- Review sample size adequacy and statistical power
- Classify findings: critical (invalidates results), major (weakens conclusions), minor

#### 2b. Robustness Assessment -- robustness-checker

Spawn `.claude/agents/drl/robustness-checker.md`:
- Verify all planned robustness checks were executed
- Assess whether alternative specifications meaningfully test sensitivity
- Check that all results (including unfavorable ones) are reported
- Flag any specification where sign, significance, or magnitude changed materially

#### 2c. Logical Consistency -- coherence-reviewer

Spawn `.claude/agents/drl/coherence-reviewer.md`:
- Verify results address every stated hypothesis
- Check literature review motivates the RQ and methodology
- Confirm conclusions follow from reported results
- Detect contradictions between paper sections
- Verify tables and figures are referenced and discussed

#### 2d. Citation Accuracy -- citation-checker

Spawn `.claude/agents/drl/citation-checker.md`:
- Cross-reference all \cite{} commands against `paper/Ref.bib`
- Detect missing or orphan BibTeX entries
- Verify cited claims match referenced papers
- Check BibTeX entry completeness and format consistency

#### 2e. Reproducibility -- reproducibility-verifier

Spawn `.claude/agents/drl/reproducibility-verifier.md`:
- Re-run the analysis pipeline from data to outputs
- Verify tables and figures match their source code
- Check random seeds produce deterministic results
- Validate dependency pinning (uv.lock)
- Test that `paper/compile.sh` produces a valid PDF

#### 2f. Writing Quality -- writing-quality-reviewer

Spawn `.claude/agents/drl/writing-quality-reviewer.md`:
- Assess clarity and precision of academic prose
- Check paragraph structure and logical flow
- Verify consistent terminology throughout
- Evaluate hedging language for statistical claims
- Check abstract structure (background, gap, method, findings, contribution)

### Step 3: Consolidate Findings

1. Collect all reviewer findings
2. Classify by severity:
   - **Critical**: Invalidates results or methodology (blocks progress)
   - **Major**: Weakens conclusions or misses key checks (must fix)
   - **Minor**: Cosmetic or stylistic (fix if time permits)
3. Deduplicate overlapping findings across reviewers
4. Create beads issues for critical/major findings: `bd create --title="Review: ..." --priority=1`

### Step 4: Fix Critical and Major Findings

1. Address all critical findings before proceeding
2. Address all major findings before proceeding
3. Re-run affected checks after fixes
4. Minor findings may be deferred to synthesis phase

## Gate Criteria

**Gate 4: All Checks Pass**

Before proceeding to synthesis, verify ALL of:

| Criterion | Verification |
|-----------|-------------|
| No critical findings unresolved | `bd list --status=open` shows no P0 review issues |
| No major findings unresolved | `bd list --status=open` shows no P1 review issues |
| Statistical methodology sound | Methodology-reviewer confirms: (a) identification strategy stated, (b) standard error clustering justified, (c) coefficient signs match theory, (d) no untested endogeneity concerns |
| Robustness checks complete | Robustness-checker confirms: at least 2 alternative specifications per main model executed and reported |
| Paper logically consistent | Coherence-reviewer confirms: every hypothesis has a corresponding result, no section contradictions |
| All citations resolve | `grep -ci "undefined" paper/main.log` returns 0 |
| Analysis reproducible | Reproducibility-verifier confirms: `uv run python -m pytest` passes and re-running pipeline produces identical outputs |
| Writing meets standards | Writing-quality-reviewer confirms: abstract has background/gap/method/findings/contribution structure |
| Tests pass | `uv run python -m pytest` exits 0 |


## Handoff Checklist

| Output | Location | Format | Next Phase Retrieval |
|--------|----------|--------|---------------------|
| Review findings report | Beads issue notes or dedicated review doc | Severity-classified list: critical / major / minor | synthesis reads findings to verify all resolved |
| Fixed paper sections | `paper/sections/*.tex` (updated in place) | LaTeX with corrections applied | synthesis reads final paper sections end-to-end |
| Fixed analysis outputs | `paper/outputs/tables/` and `paper/outputs/figures/` (updated) | Corrected LaTeX tables and figures | synthesis compiles paper with corrected outputs |
| Review beads issues | Beads (`bd list`) | P0/P1 review issues all closed | synthesis verifies `bd list --status=open` shows only the epic |

## Memory Integration

- `drl search` before review for known issues
- Calibrate each reviewer with relevant past findings
- `drl learn` after novel findings or corrections

## Failure and Recovery

If the review phase fails mid-execution:

1. **A reviewer subagent fails** (crashes, returns no findings):
   - Re-spawn the failed reviewer individually -- other reviewer results are preserved
   - If the same reviewer fails twice, skip it and note the gap in beads

2. **Critical finding cannot be resolved**:
   - Log the finding to `docs/decisions/` using the ADR template (`docs/decisions/0000-template.md`) with the attempted resolution. Use `/drl:decision` for guided logging
   - Flag as a beads issue: `bd create --title="Unresolved: ..." --priority=1`
   - Use `AskUserQuestion` to escalate to the researcher

3. **Tests fail after fixes**:
   - Revert the fix that broke tests and try a different approach
   - Do not proceed to synthesis with failing tests

4. **Partial review** (some reviewers complete, agent interrupted):
   - Check which reviewers have reported findings
   - Re-spawn only the missing reviewers -- do not re-run completed ones

## Common Pitfalls

- Running reviewers sequentially instead of in parallel
- Not classifying findings by severity (treating all as equal)
- Accepting methodology because "it produces significant results"
- Not re-running checks after fixing critical findings
- Skipping the writing quality review
- Not creating beads issues for deferred minor findings

## Quality Criteria

- [ ] All 6 reviewer dimensions covered in parallel
- [ ] Robustness-checker verified the robustness battery
- [ ] Findings classified by severity (critical/major/minor)
- [ ] All critical and major findings resolved
- [ ] Beads issues created for deferred items
- [ ] Writing quality assessed for publication readiness
- [ ] Memory searched and learned from
