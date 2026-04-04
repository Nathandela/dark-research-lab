---
version: "{{VERSION}}"
last-updated: "{{DATE}}"
summary: "Research infrastructure: memory, hooks, beads, knowledge, decision logging, and reproducibility"
---

# Integration

This document describes the infrastructure that makes DRL's research pipeline work. Each system below serves a specific role in producing traceable, reproducible social science research -- from literature indexing through statistical analysis to paper synthesis.

---

## Memory system

The memory system stores methodological lessons learned across research sessions. When an analysis approach fails, when a reviewer catches a statistical error, or when a robustness check reveals a better specification, that knowledge is captured so future sessions avoid the same pitfalls.

### Storage format

Memory items are stored as newline-delimited JSON in `.claude/lessons/index.jsonl`. Each line is a complete JSON object:

```json
{"id":"L-abc123","type":"lesson","trigger":"OLS estimates biased by omitted variable","insight":"Run Hausman test before choosing OLS over IV","tags":["methodology","endogeneity"],"source":"manual","context":{"tool":"cli","intent":"manual learning"},"created":"2026-02-15T10:00:00Z","confirmed":true,"severity":"high","supersedes":[],"related":[]}
```

### Indexing

The SQLite index at `.claude/.cache/lessons.sqlite` provides:

- **FTS5 full-text search** for keyword queries (`drl search`)
- **Embedding cache** for vector similarity (avoids re-computing embeddings)
- **Retrieval count tracking** for usage statistics

The index is rebuilt automatically when the JSONL changes. Force rebuild with `drl rebuild --force`.

### Search mechanisms

**Keyword search** (`drl search`): Uses SQLite FTS5 to match words in trigger, insight, and tags. Useful for finding past decisions about specific variables, methods, or data sources.

**Semantic search** (`drl check-plan`): Embeds the query text and compares cosine similarity against stored lesson embeddings. Results are ranked with configurable boosts for severity, recency, and confirmation status. Use this before starting a new analysis phase to surface relevant methodological lessons.

**Session loading** (`drl load-session`): Returns high-severity confirmed lessons for injection at session start. This ensures critical methodological constraints (e.g., "always cluster standard errors at the firm level for this dataset") are present in every session.

### Data lifecycle

| Operation | Effect |
|-----------|--------|
| `drl learn` | Appends a new item to JSONL |
| `drl update` | Appends an updated version (last-write-wins) |
| `drl delete` | Appends with `deleted: true` flag |
| `drl wrong` | Sets `invalidatedAt` (excluded from retrieval, preserved in storage) |
| `drl compact` | Removes tombstones, then rebuilds index |

---

## Claude Code hooks

Dark-research-lab installs seven hooks into `.claude/settings.json`. In the research context, the most important is the **decision-reminder hook**, which fires on phase transitions to prompt ADR logging -- ensuring methodological choices are documented as they happen, not reconstructed after the fact.

| Hook | Trigger | Action |
|------|---------|--------|
| **SessionStart** | New session or resume | Runs `drl prime` to load workflow context and high-severity lessons |
| **PreCompact** | Before context compaction | Runs `drl prime` to preserve context across compaction |
| **UserPromptSubmit** | Every user message | Detects correction/planning language, injects memory reminders; includes `decision-reminder.sh` which fires on phase transitions to prompt ADR logging |
| **PostToolUseFailure** | Bash/Edit/Write failures | After 2 failures on same file or 3 total, suggests `drl search` |
| **PostToolUse** | After successful tool use | Resets failure tracking; tracks skill file reads for phase guard |
| **PreToolUse** | During cook-it phases | Enforces phase gates -- prevents jumping ahead in the workflow |
| **Stop** | Session end | Enforces phase gates -- blocks stop if an active cook-it phase gate has not been verified |

### Memory usage during research sessions

**At session start**: High-severity lessons are automatically loaded via the SessionStart hook. This includes methodological constraints, data handling rules, and past analysis pitfalls.

**Before analysis planning**: Search memory and knowledge for relevant context:

```bash
drl search "instrumental variables panel data"
drl knowledge "causal inference difference-in-differences"
drl check-plan --plan "Run IV regression with firm-level clustering"
```

**After corrections**: Capture what you learned:

```bash
drl learn "Hausman test rejects OLS consistency" \
  --trigger "Reviewer flagged endogeneity concern" \
  --severity high --tags "methodology,endogeneity"
```

**At session end**: Run the compound phase to extract cross-cutting patterns:

```bash
drl compound
```

---

## Decision logging

Every methodological decision is logged to `docs/decisions/` using the ADR (Architecture Decision Record) template at `docs/decisions/0000-template.md`. This is a core research feature -- it creates an auditable trail of why each analytical choice was made.

### What gets logged

- Statistical method choices (e.g., OLS vs. IV regression, fixed vs. random effects)
- Data source selections and exclusion criteria
- Variable operationalization decisions (how abstract concepts become measurable variables)
- Sample restrictions and outlier handling
- Robustness check design choices
- Any deviation from the original research plan

### How it works

Files are named `NNNN-slug.md` (e.g., `0001-use-iv-for-endogeneity.md`) and follow a structured template:

```markdown
# [Decision Title]

## Context
[What methodological issue required a decision?]

## Decision
[What was chosen?]

## Rationale
[Why this choice? What evidence or literature supports it?]

## Consequences
[Trade-offs accepted]

## Alternatives Considered
[What else was evaluated and why it was rejected]
```

### Automated reminders

The `decision-reminder.sh` hook fires automatically on `UserPromptSubmit` when a phase transition is detected. It reads `.claude/.drl-phase-state.json` to track the current phase and emits a reminder to log decisions. This is a shell hook that runs automatically -- no agent action required.

Use `/drl:decision` for guided decision logging during any phase.

---

## Literature integration

DRL indexes literature PDFs and methodology documents for retrieval during research sessions.

### Indexing

```bash
drl index                    # Process PDFs in literature/pdfs/
```

This extracts text from PDFs (via PyMuPDF), chunks the content, computes embeddings, and stores everything in the knowledge database. The indexed content becomes searchable alongside project documentation.

### Searching

```bash
drl knowledge "causal inference"           # Semantic search over indexed docs
drl knowledge "difference-in-differences"  # Returns relevant passages
```

The knowledge system indexes both literature PDFs (from `literature/pdfs/`) and methodology documentation (from `docs/research/`). Results include source references so findings can be traced back to specific papers or documents.

### Research workflow integration

- **Spec-dev phase**: `drl knowledge` surfaces relevant literature when formulating research questions
- **Work phase**: the writing sub-skill checks `literature/notes/` and runs `drl knowledge` for citation material
- **Review phase**: citation-checker and methodology-reviewer agents query indexed literature to verify claims

---

## Beads integration

Dark-research-lab uses beads (`bd`) to track research epics and tasks -- not software features, but research phases like "Run IV regressions for Table 3" or "Write methodology section."

```bash
bd ready                          # Find available research tasks
bd show <id>                      # View task details (includes research context)
bd create --title="..." --type=task --priority=2
bd update <id> --status=in_progress
bd close <id>
bd sync                           # Sync with git remote
```

The plan phase creates Review and Compound blocking tasks that depend on work tasks. This ensures these quality gates surface via `bd ready` after analysis work completes, surviving context compaction.

### Research epics

A typical research epic contains:

- **Acceptance Criteria**: derived from the research specification (e.g., "IV first-stage F-stat > 10")
- **Verification Contract**: records the analysis profile, touched surfaces, principal risks, and required evidence
- **Phase notes**: updated at each transition to track progress through the pipeline

### Verification gates

Before closing an epic, verify all gates pass:

```bash
drl verify-gates <epic-id>
```

This checks that a Review task and Compound task both exist and are closed.

---

## Reproducibility

DRL enforces reproducibility at every level of the analysis pipeline.

### Fixed seeds

All stochastic processes -- bootstrap, simulation, imputation, sample splitting -- use documented random seeds. The QA engineer agent verifies output determinism by running the pipeline twice and comparing results.

### Environment capture

Python dependencies are locked via `uv.lock`, ensuring the exact package versions used in analysis are recorded and reproducible. The `drl doctor` command checks that the environment matches the lockfile.

### Reproducibility manifest

After analysis completes, the work-analysis sub-skill generates a reproducibility manifest:

```bash
uv run python -m src.orchestrators.repro
```

This captures the full pipeline state: data checksums, package versions, random seeds, and execution order.

### Review enforcement

The paper review fleet includes a dedicated `reproducibility-verifier` agent that checks:

- Random seeds are pinned and documented
- Dependencies are locked
- Pipeline produces identical outputs across runs
- Methods section enables replication by another researcher using only the paper

---

## For AI agents

### Integrating into CLAUDE.md

Add a reference to dark-research-lab in your project's `.claude/CLAUDE.md`:

```markdown
## References

- docs/drl/README.md -- Dark-research-lab overview and getting started
```

The `drl init` command does this automatically.

### Session completion checklist

```bash
drl verify-gates <epic-id>    # Verify review + compound tasks closed
git status                        # Check what changed
git add <files>                   # Stage code changes
bd sync                           # Commit beads changes
git commit -m "..."               # Commit code
bd sync                           # Commit any new beads changes
git push                          # Push to remote
```

Work is not complete until `git push` succeeds.
