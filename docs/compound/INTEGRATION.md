---
version: "2.6.1"
last-updated: "2026-04-03"
summary: "Memory system, hooks, beads integration, and agent guidance"
---

# Integration

Deep integration topics for dark-research-lab: memory system internals, Claude Code hooks, beads workflow, and agent guidance.

---

## Memory system

### Storage format

Memory items are stored as newline-delimited JSON in `.claude/lessons/index.jsonl`. Each line is a complete JSON object:

```json
{"id":"L-abc123","type":"lesson","trigger":"Shell injection via execSync","insight":"Use execFileSync with array args","tags":["security"],"source":"manual","context":{"tool":"cli","intent":"manual learning"},"created":"2026-02-15T10:00:00Z","confirmed":true,"severity":"high","supersedes":[],"related":[]}
```

### Indexing

The SQLite index at `.claude/.cache/lessons.sqlite` provides:

- **FTS5 full-text search** for keyword queries (`drl search`)
- **Embedding cache** for vector similarity (avoids re-computing embeddings)
- **Retrieval count tracking** for usage statistics

The index is rebuilt automatically when the JSONL changes. Force rebuild with `drl rebuild --force`.

### Search mechanisms

**Keyword search** (`drl search`): Uses SQLite FTS5 to match words in trigger, insight, and tags.

**Semantic search** (`drl check-plan`): Embeds the query text and compares cosine similarity against stored lesson embeddings. Results are ranked with configurable boosts for severity, recency, and confirmation status.

**Session loading** (`drl load-session`): Returns high-severity confirmed lessons for injection at session start.

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

Dark-research-lab installs seven hooks into `.claude/settings.json`:

| Hook | Trigger | Action |
|------|---------|--------|
| **SessionStart** | New session or resume | Runs `drl prime` to load workflow context and high-severity lessons |
| **PreCompact** | Before context compaction | Runs `drl prime` to preserve context across compaction |
| **UserPromptSubmit** | Every user message | Detects correction/planning language, injects memory reminders |
| **PostToolUseFailure** | Bash/Edit/Write failures | After 2 failures on same file or 3 total, suggests `drl search` |
| **PostToolUse** | After successful tool use | Resets failure tracking; tracks skill file reads for phase guard |
| **PreToolUse** | During cook-it phases | Enforces phase gates — prevents jumping ahead in the workflow |
| **Stop** | Session end | Enforces phase gates — blocks stop if an active cook-it phase gate has not been verified |

### Memory usage during sessions

**At session start**: High-severity lessons are automatically loaded via the SessionStart hook.

**Before planning**: Search memory for relevant context:

```bash
drl search "feature area keywords"
drl knowledge "architecture topic"
drl check-plan --plan "description of what you are about to implement"
```

**After corrections**: Capture what you learned:

```bash
drl learn "The insight" --trigger "What happened" --severity medium
```

**At session end**: Run the compound phase to extract patterns:

```bash
drl compound
```

---

## Beads integration

Dark-research-lab works with beads (`bd`) for issue tracking:

```bash
bd ready                          # Find available tasks
bd show <id>                      # View task details
bd create --title="..." --type=task --priority=2
bd update <id> --status=in_progress
bd close <id>
bd sync                           # Sync with git remote
```

The plan phase creates Review and Compound blocking tasks that depend on work tasks. This ensures these phases surface via `bd ready` after work completes, surviving context compaction.

### Verification gates

Before closing an epic, verify all gates pass:

```bash
drl verify-gates <epic-id>
```

This checks that a Review task and Compound task both exist and are closed.

---

## For AI agents

### Integrating into CLAUDE.md

Add a reference to dark-research-lab in your project's `.claude/CLAUDE.md`:

```markdown
## References

- docs/compound/README.md -- Dark-research-lab overview and getting started
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
