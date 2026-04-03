---
title: "Thin wrapper command pattern for /drl:* namespace"
status: accepted
date: 2026-04-03
deciders: ["Nathan"]
---

# Thin Wrapper Command Pattern for /drl:* Namespace

## Context

DRL needs 8 slash commands (/drl:onboard, /drl:flavor, /drl:cook-it, /drl:architect, /drl:lit-review, /drl:decision, /drl:compile, /drl:status) to expose research workflows to the user. The compound-agent project already established a thin-wrapper pattern where commands contain no logic and simply redirect to SKILL.md files.

## Decision

All 8 /drl:* commands follow the thin-wrapper pattern: YAML frontmatter (name, description, argument-hint) + $ARGUMENTS passthrough + mandatory instruction to read the corresponding SKILL.md. Commands live at `.claude/commands/drl/` and skills at `.claude/skills/drl/`.

Two new substantial skills (flavor and onboard) implement the flavor customization interview and onboarding wizard respectively. Flavor includes H2 mitigations (git commit before edit, atomic write via temp+rename).

## Consequences

### Positive
- Consistent with compound-agent's established pattern
- All logic centralized in SKILL.md files (single source of truth)
- Commands are trivially testable (file existence + format checks)

### Negative
- Adding a new command always requires both a command file and a skill file/directory

## Alternatives Considered

### Inline command logic
- Pros: Fewer files, simpler structure
- Cons: Breaks compound-agent convention, harder to test, logic split between command and skill
- Why rejected: Consistency with established patterns outweighs file count reduction
