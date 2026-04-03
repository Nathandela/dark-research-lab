# DRL -- Dark Research Lab

Autonomous research paper factory for social science. Turn a git repo into a
reproducible academic paper with AI-driven analysis, literature indexing, and
LaTeX compilation.

## Install

```bash
uv pip install dark-research-lab
```

Requires Python 3.10+.

## Quick Start

```bash
# Initialize a new research project
drl setup

# Walk through configuration
/drl:onboard

# Customize for your field (labor economics, political science, etc.)
/drl:flavor

# Index literature -- drop PDFs into literature/pdfs/, then:
drl index

# Decompose your research question into epics
/drl:architect

# Run the full pipeline (spec -> plan -> work -> review -> synthesis)
drl loop
```

## How It Works

DRL wraps [compound-agent](https://github.com/Nathandela/compound-agent) with
research-specific skills, agents, and guardrails:

```
Researcher
    |
    v
 drl CLI (Go binary in a Python wheel)
    |
    +-- Claude Code (executes skills/agents)
    +-- Beads (epic tracking with dependency graphs)
    +-- Literature RAG (PDF extraction + embedding via ca-embed)
    +-- LaTeX toolchain (3-pass pdflatex + bibtex)
    +-- Advisory Fleet (optional: Gemini, Codex reviewers)
```

Each research question passes through a **cook-it cycle**:
1. **Spec** -- research question, hypotheses, literature gap
2. **Plan** -- methodology, variables, statistical models
3. **Work** -- analysis, tables, figures, section drafting
4. **Review** -- methodology audit + external model review
5. **Synthesis** -- lessons captured, paper section finalized

Every methodological decision is logged to `docs/decisions/` for full
traceability. A reproducibility package (lockfile + data manifest + run script)
is generated at compilation time.

## Project Structure

```
paper/          LaTeX source and compiled outputs
src/            Analysis scripts
literature/     PDFs and indexed knowledge base
docs/           Decisions, specs, agent notes
tests/          Test suite
.claude/        Skills, agents, hooks, commands
```

## Commands

| Command | Purpose |
|---------|---------|
| `drl setup` | Initialize or update project templates |
| `drl index` | Index literature PDFs for RAG search |
| `drl loop` | Run infinity loop over all epics |
| `/drl:compile` | Compile LaTeX paper + reproducibility package |
| `/drl:flavor` | Customize skills for your research field |
| `/drl:onboard` | Guided first-time setup |
| `/drl:architect` | Decompose research question into epics |

## Documentation

- [System Specification](docs/specs/drl-package.md)
- [Architecture Decisions](docs/decisions/)
- [Agent Configuration](AGENTS.md)

## License

[MIT](LICENSE)
