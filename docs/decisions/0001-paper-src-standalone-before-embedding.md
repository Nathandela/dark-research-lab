---
title: "Paper/src scaffolding as standalone files before Go embedding"
status: accepted
date: 2026-04-03
deciders: ["Nathan Delacretaz"]
---

# Paper/Src Scaffolding as Standalone Files Before Go Embedding

## Context

Epic 3 creates the LaTeX paper template and Python analysis scaffolding. The spec (E1) says `drl setup` shall install these templates, which implies embedding them in the Go binary. However, the Go binary embedding mechanism is a separate concern from getting the template files correct and tested.

## Decision

Create paper/ and src/ directly in the project repo as standalone files. Defer Go binary embedding to a later task that links these files into the `drl setup` flow.

## Consequences

### Positive
- Faster iteration on template content without Go rebuild cycles
- Tests can validate files directly without running `drl setup`
- Clear separation: Epic 3 = correct templates, later = embedding

### Negative
- `drl setup` won't install these templates until embedding is done

## Alternatives Considered

### Embed directly in Go binary during Epic 3
- Pros: Full E1 compliance immediately
- Cons: Couples template correctness testing with Go build, slower iteration
- Why rejected: Template content and Go embedding are orthogonal concerns
