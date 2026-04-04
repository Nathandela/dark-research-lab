---
name: Work Code
description: TDD-based code implementation for analysis pipeline and infrastructure
---

# Work Code Sub-Skill

## Overview

Execute code tasks using strict Test-Driven Development. Write tests first, then implement the minimum code to pass them. This sub-skill is invoked by the work router -- it does not run standalone.

## Agent Delegation

Deploy test-writer + implementer agents via AgentTeam:

- **Test-writer**: `.claude/skills/drl/agents/test-writer/SKILL.md` -- writes tests from acceptance criteria
- **Implementer**: `.claude/skills/drl/agents/implementer/SKILL.md` -- writes the minimum code to pass tests

## Methodology

### Step 1: Understand the Task

1. Read the task description and acceptance criteria from beads
2. Identify which modules are affected (data loaders, analysis functions, visualizations, orchestrators)
3. Check existing code and tests for context

### Step 2: Write Tests First

Spawn the test-writer agent:

1. Translate acceptance criteria into test cases
2. Write tests in `tests/` following existing patterns (`conftest.py` for fixtures)
3. Use clear test names: `test_<behavior>_<condition>_<expected>`
4. Include edge cases and error conditions

### Step 3: Verify Tests Fail (Red)

Run the test suite to confirm tests fail for the right reason (missing implementation, not syntax errors):

```bash
uv run python -m pytest tests/<test_file>.py -v
```

### Step 4: Implement (Green)

Spawn the implementer agent:

1. Write the minimum code that passes the failing tests
2. Pass one test at a time -- do not write ahead
3. Never modify tests to make them pass

### Step 5: Verify and Refactor

1. Run the full test suite for regressions: `uv run python -m pytest`
2. Refactor only when all tests are green
3. Commit incrementally as tests pass

## Verification Gate

- `{{QUALITY_GATE_TEST}}` passes (full test suite green)
- `{{QUALITY_GATE_LINT}}` passes (no lint violations)
- No regressions in existing tests

## Scope

- Data loaders: `src/data/`
- Analysis functions: `src/analysis/`
- Visualization: `src/visualization/`
- Orchestrators: `src/orchestrators/`
- Any Python infrastructure supporting the research pipeline
