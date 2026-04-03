---
version: "2.6.1"
last-updated: "2026-04-03"
summary: "Overview and getting started guide for dark-research-lab"
---

# Dark Research Lab

A learning system for Claude Code that captures, indexes, and retrieves lessons learned during development sessions -- so the same mistakes are not repeated.

---

## What is dark-research-lab?

Dark-research-lab is a Go CLI that integrates with Claude Code. When Claude makes a mistake and gets corrected, or discovers a useful pattern, that knowledge is stored as a **memory item** in `.claude/lessons/index.jsonl`. Future sessions search this memory before planning and implementing.

The system uses:

- **JSONL storage** (`.claude/lessons/index.jsonl`) as the git-tracked source of truth
- **SQLite + FTS5** (`.claude/.cache/lessons.sqlite`) as a rebuildable search index
- **Semantic embeddings** (drl-embed Rust daemon with local model) for vector similarity search
- **Claude Code hooks** to inject memory at session start, before compaction, and on tool failures

Memory items have four types: `lesson`, `solution`, `pattern`, and `preference`. Each has a trigger, an insight, tags, severity, and optional citations.

---

## Quick start

```bash
# Initialize in your project:
drl init

# Full setup (includes embedding model download):
drl setup

# Verify installation:
drl doctor
```

### What `init` does

1. Creates `.claude/lessons/` directory and empty `index.jsonl`
2. Updates `AGENTS.md` with a dark-research-lab section
3. Adds a reference to `.claude/CLAUDE.md`
4. Creates `.claude/plugin.json` manifest
5. Installs agent templates, workflow commands, phase skills, and agent role skills
6. Installs a git pre-commit hook (lesson capture reminder)
7. Installs Claude Code hooks (SessionStart, PreCompact, UserPromptSubmit, PostToolUseFailure, PostToolUse, PreToolUse, Stop)

`setup` does everything `init` does. The embedding model is managed separately by the embed daemon.

---

## Directory structure

```
.claude/
  CLAUDE.md                    # Project instructions (always loaded)
  dark-research-lab.json          # Config (created by `drl reviewer enable`)
  settings.json                # Claude Code hooks
  plugin.json                  # Plugin manifest
  agents/compound/             # Subagent definitions
  commands/compound/           # Slash commands (spec-dev, plan, work, review, compound, cook-it, agentic-audit, agentic-setup)
  skills/compound/             # Phase skills + agent role skills
  lessons/
    index.jsonl                # Memory items (git-tracked source of truth)
  .cache/
    lessons.sqlite             # Rebuildable search index (.gitignore)
docs/compound/
  research/                    # PhD-level research docs for agent knowledge
```

---

## Quick reference

| Task | Command |
|------|---------|
| Capture a lesson | `drl learn "insight" --trigger "what happened"` |
| Search memory | `drl search "keywords"` |
| Search docs knowledge | `drl knowledge "query"` |
| Check plan against memory | `drl check-plan --plan "description"` |
| View stats | `drl stats` |
| Run full workflow | `/compound:cook-it <epic-id>` |
| Health check | `drl doctor` |

---

## Further reading

- [WORKFLOW.md](WORKFLOW.md) -- The 5-phase development workflow and cook-it orchestrator
- [CLI_REFERENCE.md](CLI_REFERENCE.md) -- Complete CLI command reference
- [SKILLS.md](SKILLS.md) -- Phase skills and agent role skills
- [INTEGRATION.md](INTEGRATION.md) -- Memory system, hooks, beads, and agent guidance
