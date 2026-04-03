<!-- dark-research-lab:start -->
## Dark Research Lab Integration

This project uses dark-research-lab for session memory via **CLI commands**.

### CLI Commands (ALWAYS USE THESE)

**You MUST use CLI commands for lesson management:**

| Command | Purpose |
|---------|---------|
| `drl search "query"` | Search lessons - MUST call before architectural decisions; use anytime you need context |
| `drl knowledge "query"` | Semantic search over project docs - MUST call before architectural decisions; use keyword phrases, not questions |
| `drl learn "insight"` | Capture lessons - use AFTER corrections or discoveries |
| `drl list` | List all stored lessons |
| `drl show <id>` | Show details of a specific lesson |
| `drl wrong <id>` | Mark a lesson as incorrect |

### Mandatory Recall

You MUST call `drl search` and `drl knowledge` BEFORE:
- Architectural decisions or complex planning
- Patterns you've implemented before in this repo
- After user corrections ("actually...", "wrong", "use X instead")

**NEVER skip search for complex decisions.** Past mistakes will repeat.

Beyond mandatory triggers, use these commands freely — they are lightweight queries, not heavyweight operations. Uncertain about a pattern? `drl search`. Need a detail from the docs? `drl knowledge`. The cost of an unnecessary search is near-zero; the cost of a missed one can be hours.

### Capture Protocol

Run `drl learn` AFTER:
- User corrects you
- Test fail -> fix -> pass cycles
- You discover project-specific knowledge

**Workflow**: Search BEFORE deciding, capture AFTER learning.

### Quality Gate

Before capturing, verify the lesson is:
- **Novel** - Not already stored
- **Specific** - Clear guidance
- **Actionable** (preferred) - Obvious what to do

### Never Edit JSONL Directly

**WARNING: NEVER edit .claude/lessons/index.jsonl directly.**

The JSONL file requires proper ID generation, schema validation, and SQLite sync.
Use CLI (`drl learn`) — never manual edits.

See [documentation](https://github.com/Nathandela/dark-research-lab) for more details.
<!-- dark-research-lab:end -->
