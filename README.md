# Dark Research Lab

> DRL is an opinionated agent harness for long-duration autonomous research. It turns a git repo into a structured research environment where AI agents can work across many sessions -- from literature review to compiled LaTeX paper. Built on [compound-agent](https://github.com/Nathandela/compound-agent). Fully local. Everything in git.

[![PyPI version](https://img.shields.io/pypi/v/dark-research-lab)](https://pypi.org/project/dark-research-lab/)
[![license](https://img.shields.io/pypi/l/dark-research-lab)](LICENSE)
[![Go](https://img.shields.io/badge/Go-1.24+-00ADD8)](https://go.dev/)

```bash
# Install
uv tool install dark-research-lab
brew install beads   # or: npm install -g @beads/bd

# Set up a project
mkdir my-paper && cd my-paper && git init
drl setup

# Add data and literature
cp ~/data/*.csv data/input/
cp ~/papers/*.pdf literature/pdfs/
drl index

# Run the pipeline
/drl:architect          # Decompose research question into epics
/drl:cook-it <epic-id>  # Run full 5-phase cycle on one epic

# Or run autonomously -- the architect can generate the loop for you
drl loop --force && screen -dmS loop ./infinity-loop.sh
```

> **Warning:** The infinity loop runs unattended and will consume API credits. Set a spending limit on your Anthropic account and monitor with `drl watch`.

---

AI research agents forget everything between sessions. They re-derive methodology choices, miss literature they already read, and repeat statistical mistakes they made last week. DRL fixes this by giving agents persistent structure: indexed literature, decision logs, phase gates, and memory that carries across sessions. It is designed for empirical social science -- economics, political science, sociology, public health -- where the deliverable is a journal-quality paper with regression tables, identification strategies, and robustness batteries.

## What gets installed

`drl setup` scaffolds a complete research environment into your repository:

| Component | What ships |
|-----------|-----------|
| 27 specialized agents | Methodology reviewer, robustness checker, writing quality reviewer, citation checker, literature analyst, reproducibility verifier, and more |
| 22 skills | Phase instructions that chain agents through a structured pipeline |
| 16 knowledge documents | PhD-level references covering econometrics, causal inference, identification, robustness, writing conventions, Python architecture |
| LaTeX paper scaffold | 7 section files, compilation script, table/figure output directories |
| Python analysis skeleton | Modules for data loading, econometrics, descriptive statistics, robustness, and visualization |
| Literature indexing | PDF extraction, chunking, and semantic search over your source papers |
| Decision logging | ADR templates for every methodological choice |

This is not a chatbot wrapper. It is the environment your research agents run inside.

## How it works

Each research question passes through a **cook-it cycle** -- five phases with enforcement gates between them. Agents cannot skip ahead. Each phase must pass its gate before the next begins.

```
  Spec ──→ Plan ──→ Work ──→ Review ──→ Synthesis
   │         │        │         │           │
   │         │        │         │           └─ Compile paper, capture lessons
   │         │        │         └─ Multi-agent audit (methodology, stats, writing)
   │         │        └─ Run regressions, generate tables/figures, draft sections
   │         └─ Methodology design, variable operationalization, analysis plan
   └─ Socratic refinement of research question, hypotheses, identification strategy
```

Between sessions, **compound-agent's memory system** persists what was learned -- statistical pitfalls, data quality issues, specification choices that worked or failed. Future sessions load these automatically. The **knowledge base** (16 documents covering econometrics, causal inference, identification, robustness, writing) is always available to agents during analysis and review.

Every methodological decision is logged to `docs/decisions/` using ADR templates. When you return weeks later, or when a reviewer asks "why fixed effects instead of random effects?", the answer is there.

## Is this for you?

**"My agent keeps picking the wrong estimator."**
16 knowledge documents on econometrics, causal inference, and identification are indexed and searchable. Agents consult them during planning and review -- not from memory, but by reading the actual documents each time.

**"I need reproducible results."**
A reproducibility manifest captures data checksums, package versions, and random seeds. The analysis skeleton enforces a clean data pipeline: raw data in `data/input/` (read-only by convention), all transformations produce new files in `data/output/`.

**"Reviews keep finding the same methodology issues."**
27 specialized agents run in parallel during review: methodology, robustness, writing quality, citations, coherence, reproducibility. Findings feed back as lessons that surface in future sessions.

**"I want to hand off a research question and come back to a draft."**
`/drl:architect` decomposes your question into epics. `drl loop` processes them autonomously across sessions. You can disconnect and come back later.

**"I need to track why every decision was made."**
Decision logging is mandatory, not optional. Every statistical method choice, data exclusion criterion, and variable operationalization gets an ADR entry.

**"My field has specific conventions."**
`/drl:flavor` customizes agents, review criteria, and default robustness checks for your research domain. A labor economist and a public health researcher have different norms.

## Install

Requires Python 3.10+ and [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

```bash
# Install DRL
uv tool install dark-research-lab

# Install beads (task tracker for epics and dependencies)
brew install beads                 # macOS / Linux -- recommended
# Alternative: npm install -g @beads/bd    # note the scoped name; unscoped "beads" on npm is a different project

# Optional: external reviewers for multi-model review
npm install -g @google/gemini-cli    # Gemini
npm install -g @openai/codex         # Codex
```

Verify: `drl about`

## Quick start

### 1. Create and scaffold

```bash
mkdir my-paper && cd my-paper && git init
drl setup
```

`drl setup` creates the full directory structure, installs agents, skills, commands, hooks, knowledge docs, the LaTeX template, and the Python skeleton. It also creates `.venv/` and installs Python dependencies. Takes about 30 seconds.

### 2. Protect and place your data

**Never give DRL your only copy of any dataset.** Raw data goes in `data/input/`, treated as read-only by convention. Keep originals elsewhere.

```bash
cp ~/data/survey_2024.csv data/input/
cp ~/data/admin_records.dta data/input/
```

### 3. Add your literature

```bash
cp ~/papers/*.pdf literature/pdfs/
drl index
```

This extracts text, chunks it, and stores everything in a local knowledge database. Re-run `drl index` any time you add more papers.

### 4. Configure for your field

```
/drl:flavor
```

Customizes agents and review criteria for your specific research domain.

### 5. Decompose your research question

```
/drl:architect
```

The architect asks clarifying questions, searches your indexed literature, helps formulate hypotheses, and decomposes the project into 4-6 epics.

### 6. Run the pipeline

```bash
# Interactive: run one epic at a time
/drl:cook-it <epic-id>

# Autonomous: process all epics unattended
drl loop --force && screen -dmS loop ./infinity-loop.sh
```

### 7. Commit

```bash
git add -A && git commit -m "Initialize research project with DRL"
```

See [docs/drl/ONBOARDING.md](docs/drl/ONBOARDING.md) for the full walkthrough.

## Architecture

```
Researcher
    │
    ▼
 drl CLI (Go binary in a Python wheel)
    │
    ├── Claude Code (executes skills/agents)
    ├── compound-agent (memory + structured workflows)
    ├── Beads (epic tracking with dependency graphs)
    ├── Literature RAG (PDF extraction → chunking → search)
    ├── LaTeX toolchain (3-pass pdflatex + bibtex)
    └── Advisory Fleet (optional: Gemini, Codex reviewers)
```

DRL wraps [compound-agent](https://github.com/Nathandela/compound-agent) with research-specific skills, agents, and guardrails. Compound-agent provides the memory system, hooks, and workflow engine. DRL adds domain knowledge (econometrics, causal inference), research-specific agents (methodology reviewer, robustness checker), and the literature pipeline.

## Project structure

```
paper/              LaTeX source and compiled outputs
  sections/         Individual paper sections (intro, methodology, results, ...)
  outputs/tables/   Machine-generated regression tables
  outputs/figures/  Machine-generated figures
src/                Python analysis scripts
  data/             Loaders and cleaners
  analysis/         Econometrics, descriptive stats, robustness
  visualization/    Figure generation
  literature/       PDF extraction module
literature/
  pdfs/             Source papers
  notes/            Auto-generated reading summaries
data/
  input/            Raw data (read-only by convention)
  output/           Transformed data
docs/
  decisions/        ADR entries for every methodological choice
  specs/            Research specifications
tests/              Test suite
.claude/            Skills, agents, hooks, commands
```

## Commands

### CLI

| Command | Purpose |
|---------|---------|
| `drl setup` | Initialize or update project (+ Python venv + dependencies) |
| `drl index` | Index literature PDFs for agent search |
| `drl loop` | Generate infinity loop script for autonomous epic processing |
| `drl doctor` | Check project health (hooks, beads, Python venv, deps) |
| `drl knowledge "query"` | Search indexed knowledge documents |
| `drl search "query"` | Search lessons and memory |
| `drl learn "insight"` | Capture a lesson |
| `drl stats` | Show database health and statistics |
| `drl about` | Show version and info |

### Slash commands (in Claude Code)

| Command | Purpose |
|---------|---------|
| `/drl:architect` | Decompose research question into epics |
| `/drl:cook-it <epic-id>` | Run full 5-phase pipeline on one epic |
| `/drl:flavor` | Customize skills for your research field |
| `/drl:compile` | Compile LaTeX paper + reproducibility package |
| `/drl:onboard` | Guided first-time setup |
| `/drl:decision` | Log a methodological decision |
| `/drl:status` | Check pipeline and epic status |
| `/drl:lit-review` | Structured literature review |

## The long-duration harness

Unlike a one-shot script, DRL is designed for research campaigns that span days or weeks across many sessions:

- **Beads** tracks research progress across sessions. When a session ends mid-pipeline, the next session picks up where it left off.
- **Decision logging** creates a permanent record of every methodological choice.
- **The memory system** captures lessons learned during analysis. Future sessions load them automatically.
- **Phase gates** enforce quality. You cannot skip phases, and gate conditions are checked mechanically.
- **The knowledge base** is always available to agents. They read the actual documents each time, not from memory.

## Documentation

- [Onboarding Guide](docs/drl/ONBOARDING.md) -- Full setup walkthrough
- [Workflow Reference](docs/drl/WORKFLOW.md) -- The 5-phase pipeline in detail
- [Skills Reference](docs/drl/SKILLS.md) -- All skills and slash commands
- [CLI Reference](docs/drl/CLI_REFERENCE.md) -- Complete CLI reference
- [Integration Guide](docs/drl/INTEGRATION.md) -- Hooks, beads, memory, and reproducibility

## FAQ

**Q: How is this different from using Claude Code directly?**
A: Claude Code is a general-purpose coding assistant. DRL adds research-specific structure: methodology knowledge, literature indexing, decision logging, phase gates, and 27 specialized agents that understand empirical social science.

**Q: Does this work offline?**
A: Literature indexing and knowledge search work locally. The AI agents require Claude Code (which calls the Anthropic API). Optional external reviewers (Gemini, Codex) require their own API access.

**Q: What fields does this support?**
A: It targets empirical social science: economics, political science, sociology, public health. The `/drl:flavor` command customizes for your specific subfield. The standard deliverable is a journal-quality paper with regression tables and robustness batteries.

**Q: Can I use my own LaTeX template?**
A: Yes. DRL scaffolds a default template, but you can replace `paper/main.tex` and the section files. The compilation script and output directories still work.

**Q: What about data privacy?**
A: Everything is local and git-tracked. No data leaves your machine except through the AI API calls you explicitly authorize. Keep sensitive data out of git via `.gitignore`.

## License

[MIT](LICENSE)
