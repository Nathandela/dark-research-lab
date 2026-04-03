# Advisory Fleet Brief -- Template Migration

**Advisors consulted**: Scalability & Performance (Gemini), Organizational & Delivery (Codex)
**Advisors unavailable**: Security & Reliability / Simplicity & Alternatives (Claude -- timed out)

---

## P0 Concerns

- **Testing bottleneck in Epic 6** (Gemini): Deferring all test updates to a final monolithic Epic 6 means regressions from Epics 2-5 compound and are discovered late. **Suggestion**: Shift testing left -- require Epics 2-5 to update their own Go template tests and assertions. Reserve Epic 6 for test/ fixture regeneration and end-to-end Python tests only.

- **Epic 1 as global blocker** (Codex): Epic 1 (Go Namespace) blocks all parallel work. If it drags out, the entire program stalls. **Suggestion**: Keep Epic 1 mechanical and narrow -- global find-and-replace of path strings. Merge immediately to unblock.

## P1 Concerns

- **Merge conflicts on shared files** (Gemini): Parallel Epics 2-5 may touch shared config files (init.go, plugin.json). **Suggestion**: Use directory-based embedding and minimize shared registry edits.

- **Hidden dependencies between parallel epics** (Codex): Skills, hooks, scaffolding, and commands have implicit coupling. **Suggestion**: Define explicit contracts early (phase names, skill paths, hook events, scaffold paths).

- **Template shape is a public API** (Codex): Once `drl setup` writes files to user repos, the directory layout becomes a contract. **Suggestion**: Version the template schema from day one.

- **Cognitive load in large epics** (Codex): Some epics span too many concepts. **Suggestion**: Keep each epic tightly focused on one artifact type.

## P2 Concerns

- **Content-to-engine coupling** (Gemini): Embedding volatile prompt files in the Go binary means every skill tweak needs a full Go rebuild. Acceptable now, consider decoupling later.

- **Cross-ecosystem boundaries** (Codex): Go binary + markdown skills + shell hooks + Python scaffolding = context switching. Keep ownership boundaries hard.

## Strengths (consensus)

- Single-developer ownership keeps coordination cost near zero (Codex)
- Go embed is highly optimized for text files -- negligible binary bloat (~300-500KB) (Gemini)
- `drl setup` executes in milliseconds with embedded templates (Gemini)
- Namespace isolation (drl/) prevents directory pollution (Gemini)
- Epics are conceptually separable by artifact boundary (Codex)

## Confidence Summary

| Advisor | Confidence | Justification |
|---------|-----------|---------------|
| Scalability & Performance | HIGH | Embedding text in Go is mature/performant; risks are workflow-related only |
| Organizational & Delivery | MEDIUM | Dependency list is clear but hidden couplings likely understated |
| Security & Reliability | N/A | Advisor timed out |
| Simplicity & Alternatives | N/A | Advisor timed out |

## Actionable Changes to Spec

Based on advisory feedback, the following adjustments are recommended:

1. **Shift testing left**: Epics 2-5 each include their own Go template test updates. Epic 6 becomes "Test Fixture + Python E2E Tests" only.
2. **Keep Epic 1 razor-thin**: Only Go path changes + Go path tests. No template content changes.
3. **Define inter-epic contracts upfront**: Phase names, skill paths, hook events, scaffold paths documented before Epics 2-5 start.
