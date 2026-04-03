---
title: "Research scaffolding as Go-embedded templates"
status: accepted
date: 2026-04-03
deciders: ["Nathan"]
---

# Research Scaffolding as Go-Embedded Templates

## Context

E4 requires `drl setup` to scaffold paper/, src/, literature/, docs/, and tests/ directories in new repositories. The source files already exist at the repo root and serve as the canonical templates.

## Decision

Embed the scaffolding files into the Go binary using `//go:embed all:scaffolding` and install them via five new Install functions (InstallPaperScaffolding, InstallSrcScaffolding, InstallLiteratureSetup, InstallDocsStructure, InstallTestsScaffolding). These are wired into the infrastructure tier of installTemplateGroups(), so they install on every `drl setup` invocation.

## Rationale

- Reuses the existing reconcileFile/writeSkillFile primitives for idempotent create-or-update behavior.
- The `all:` embed prefix handles .gitkeep files (dotfiles) without special-casing.
- A single `readEmbedTree` helper avoids duplicating the walk-and-extract pattern.
- Infrastructure tier ensures scaffolding is always installed regardless of --core-skill/--all-skill flags.

## Consequences

### Positive
- `drl setup` creates a complete research project structure in one command.
- Templates stay in sync with the Go binary version.

### Negative
- Binary size increases (~50KB for the template content).
- Template changes require a Go rebuild.
