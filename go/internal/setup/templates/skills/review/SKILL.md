---
name: Review
description: Multi-agent review with dual-mode detection for code and paper changes
phase: review
---

# Review Skill

## Overview

Multi-agent review that auto-detects what changed and spawns the appropriate review fleet. Code changes get code reviewers. Paper changes get research reviewers. Both get both.

## Input

- Changed files since last review (from git diff or bead notes)
- Epic context: `bd show <epic>` for acceptance criteria and verification contract
- Previous review commit hash (if any) for accurate diff range

## Methodology

### Step 1: Detect Review Mode

1. Run `git diff --name-only HEAD~N` (or compare against last review commit) to identify changed files
2. Classify changes:
   - **Code changes**: `*.py`, `*.sh`, `src/**`, `tests/**`, `*.toml`, `*.cfg`
   - **Paper changes**: `*.tex`, `*.bib`, `paper/**`
   - **Both**: files from both categories changed
3. Select review mode:
   - Code only -> spawn Code Review Fleet
   - Paper only -> spawn Paper Review Fleet
   - Both -> spawn both fleets in parallel

### Step 2: Code Review Fleet (when code files changed)

Spawn these reviewers in parallel via AgentTeam:

1. `security-reviewer` (`.claude/skills/drl/agents/security-reviewer/SKILL.md`) -- P0-P3 security audit
2. `simplicity-reviewer` (`.claude/skills/drl/agents/simplicity-reviewer/SKILL.md`) -- complexity check
3. `test-coverage-reviewer` (`.claude/skills/drl/agents/test-coverage-reviewer/SKILL.md`) -- test adequacy
4. `performance-reviewer` (`.claude/skills/drl/agents/performance-reviewer/SKILL.md`) -- efficiency check
5. `runtime-verifier` (`.claude/skills/drl/agents/runtime-verifier/SKILL.md`) -- pipeline runs end-to-end (`uv run python -m pytest`)

### Step 3: Paper Review Fleet (when paper files changed)

Spawn these reviewers in parallel via AgentTeam:

1. `methodology-reviewer` (`.claude/agents/drl/methodology-reviewer.md`) -- statistical validity
2. `coherence-reviewer` (`.claude/agents/drl/coherence-reviewer.md`) -- logical consistency
3. `writing-quality-reviewer` (`.claude/agents/drl/writing-quality-reviewer.md`) -- prose quality
4. `citation-checker` (`.claude/agents/drl/citation-checker.md`) -- citation accuracy
5. `reproducibility-verifier` (`.claude/agents/drl/reproducibility-verifier.md`) -- reproducibility
6. `argumentation-reviewer` (`.claude/agents/drl/argumentation-reviewer.md`) -- argument coherence
7. `statistical-methods-reviewer` (`.claude/agents/drl/statistical-methods-reviewer.md`) -- method audit
8. `theoretical-framing-reviewer` (`.claude/agents/drl/theoretical-framing-reviewer.md`) -- theory-question fit
9. `contribution-clarity-reviewer` (`.claude/agents/drl/contribution-clarity-reviewer.md`) -- novelty assessment
10. `robustness-checker` (`.claude/agents/drl/robustness-checker.md`) -- robustness assessment of statistical results

### Step 4: Collect and Classify Findings

1. Aggregate findings from all active fleet(s)
2. Deduplicate overlapping findings across reviewers
3. Classify by severity:
   - **Critical**: blocks progress, invalidates results or introduces security risk
   - **Major**: must address before proceeding, weakens conclusions or correctness
   - **Minor**: optional, cosmetic or stylistic improvements
4. Present findings to user grouped by fleet and severity
5. Create beads issues for Critical and Major findings: `bd create --title="Review: ..." --priority=1`

### Step 5: Resolution

- Critical and Major findings MUST be resolved before proceeding
- Create beads tasks for deferred Minor findings
- Re-run affected reviewers after fixes to verify resolution

## Gate Criteria (Gate 4)

| Criterion | Verification |
|-----------|-------------|
| No Critical findings remain | `bd list --status=open` shows no P0 review issues |
| No Major findings remain | `bd list --status=open` shows no P1 review issues |
| All reviewer outputs collected | Every spawned reviewer returned findings |
| Findings classified by severity | Each finding tagged Critical, Major, or Minor |
| Human confirmation | `AskUserQuestion` approval received |

## Handoff Checklist

| Output | Location | Format |
|--------|----------|--------|
| Review findings summary | Beads epic notes | Severity-classified list |
| Deferred issues | Beads tasks | Minor findings as tasks |

## Memory Integration

- `drl search` before starting review
- `drl learn` after discovering review patterns

## Failure and Recovery

- If a reviewer agent fails: report which reviewer failed, re-spawn it once, if still failing skip and note in findings
- If too many findings: prioritize Critical > Major, present in batches
- If partially interrupted mid-review: check which reviewers reported, re-spawn only the missing ones
- If a Critical finding cannot be resolved: log to `docs/decisions/` using ADR template, escalate via `AskUserQuestion`

## Common Pitfalls

- Running only one fleet when both code and paper changed
- Not re-running reviewers after fixes
- Proceeding with unresolved Critical findings
- Ignoring paper reviewers for "small" paper changes
- Running reviewers sequentially instead of in parallel
- Not creating beads issues for deferred Minor findings
- Treating all findings as equal severity

## Quality Criteria

- [ ] Review mode correctly detected from changed files
- [ ] Appropriate fleet(s) spawned based on detected mode
- [ ] All findings deduplicated and classified by severity
- [ ] Critical and Major findings resolved before proceeding
- [ ] Minor findings logged as beads tasks
- [ ] Affected reviewers re-run after fixes
- [ ] Human approved review results via AskUserQuestion
