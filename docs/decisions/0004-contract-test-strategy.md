---
title: "Contract tests for cross-epic integration"
status: accepted
date: 2026-04-03
deciders: ["Nathan Delacrétaz"]
---

# Contract Tests for Cross-Epic Integration

## Context

DRL is built across 7 domain epics with cross-cutting interfaces (hooks, skills, agents, commands, scaffolding paths). Breaking changes in one epic can silently break another. Epic IV requires verifying these interfaces hold.

## Decision

Use Python pytest contract tests that verify cross-epic interfaces by checking file existence, YAML validity, string references, and binary behavior. Tests live in `tests/test_integration_cross_epic.py` and cover all 9 contracts from the Epic IV specification.

## Rationale

Contract tests are lightweight (no mocking, no complex setup) and catch the most likely failure mode: references to files, paths, or commands that don't exist or have been renamed. This is the right granularity for a MEDIUM-scope integration epic.

## Consequences

### Positive
- Catches broken cross-references (renamed skills, missing agents) immediately
- Runs in under 5 seconds with the full suite
- No external dependencies beyond pytest and pyyaml

### Negative
- Tests verify structure, not runtime behavior (e.g., can't test that flavor actually commits before editing)
- Must be updated when new skills or agents are added

## Alternatives Considered

### Full end-to-end simulation tests
- Pros: Would test actual runtime behavior
- Cons: Requires mocking Claude Code, complex setup, slow execution
- Why rejected: Overkill for MEDIUM scope; structural verification catches most real failures
