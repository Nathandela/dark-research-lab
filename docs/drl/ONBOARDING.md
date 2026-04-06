# Getting Started with DRL

## What You Get

DRL is a long-duration research harness. It is not a statistical package, a paper template, or a one-shot script. It is infrastructure that supports autonomous, multi-session research campaigns -- from research question to compiled LaTeX paper.

When you run `drl setup` in a project directory, you get:

- **27 specialized AI agents** -- each handles one research task (methodology review, robustness checking, academic writing, citation verification, etc.)
- **22 skills** -- phase instructions that chain agents through a structured pipeline
- **16 knowledge documents** -- PhD-level references covering social science methodology (econometrics, causal inference, identification, robustness, writing conventions) and Python architecture (concurrency, scientific computing, packaging, performance). Agents consult these during analysis and review.
- **A LaTeX paper scaffold** -- 7 section files, compilation script, table/figure output directories
- **A Python analysis skeleton** -- modules for data loading, econometrics, descriptive statistics, robustness, and visualization
- **Decision logging infrastructure** -- ADR templates for every methodological choice
- **Literature indexing** -- PDF extraction and semantic search over your source papers

The system is designed for social science researchers doing empirical work: economics, political science, sociology, public health. The standard deliverable is a journal-quality paper with regression tables, identification strategies, and robustness batteries.

---

## Prerequisites

DRL requires four things installed on your machine:

### 1. Python 3.10+

DRL uses Python for data analysis, PDF extraction, and figure generation. Verify with `python3 --version`. Most systems have this already.

### 2. DRL itself

```bash
uv tool install dark-research-lab
```

This installs the `drl` CLI globally. Verify with `drl about`.

### 3. Claude Code

DRL's agents run inside Claude Code sessions. Install it following [the official guide](https://docs.anthropic.com/en/docs/claude-code).

### 4. Beads (task tracker)

DRL uses beads to track research epics and tasks. Each analysis step, robustness check, and paper section becomes a beads issue with dependencies and acceptance criteria.

```bash
npm install -g beads
```

Verify with `bd stats`.

### Optional: external reviewers

For multi-model review (recommended), install one or more external model CLIs:

```bash
# Gemini CLI
npm install -g @anthropic-ai/gemini-cli

# Codex CLI
npm install -g @openai/codex-cli
```

DRL detects available CLIs automatically and uses them for advisory and review fleets. If none are available, everything still works -- you just get single-model review.

---

## Setting Up a Research Project

### Step 1: Create and initialize

```bash
mkdir my-research-project && cd my-research-project
git init
drl setup
```

`drl setup` scaffolds the full directory structure, installs agents, skills, commands, hooks, knowledge docs, the LaTeX template, and the Python skeleton. It also creates a `.venv/` and installs Python dependencies (PyMuPDF for PDF extraction, Polars for data manipulation, Matplotlib for figures). This takes about 30 seconds.

### Step 2: Protect and place your data

**Critical**: never give DRL your only copy of any dataset. Raw data goes in `data/input/`, and this directory is treated as read-only by convention -- all transformations produce new files in `data/output/`. But mistakes happen, so:

1. **Keep your original data elsewhere** (external drive, cloud, institutional server). The copy in `data/input/` is a working copy.
2. Copy your datasets into `data/input/`:
   ```bash
   cp ~/data/survey_2024.csv data/input/
   cp ~/data/admin_records.dta data/input/
   ```
3. If your data is too large or too sensitive for the repo, document where it lives in `docs/decisions/0001-data-sources.md` and configure `.gitignore` accordingly.

### Step 3: Add your literature

Drop your source papers (PDFs) into `literature/pdfs/`:

```bash
cp ~/papers/*.pdf literature/pdfs/
```

Then index them so agents can search the content during analysis and review:

```bash
drl index
```

This extracts text, chunks it, computes embeddings, and stores everything in a local knowledge database. You can re-run `drl index` any time you add more papers.

### Step 4: Add your notes (optional)

If you have existing research notes, literature summaries, or preliminary analysis, place them in:

- `literature/notes/` -- structured reading notes on specific papers
- `docs/researcher_notes/` -- your working hypotheses, data exploration notes, preliminary findings

Agents read these directories during the spec and planning phases. Anything you put here becomes context for the AI.

### Step 5: Configure for your field

```
/drl:flavor
```

This interactive command customizes the agents, review criteria, and default robustness checks for your specific research domain. A labor economist, a comparative political scientist, and a public health researcher have different norms for identification, writing conventions, and what "robustness" means. Flavor adjusts for this.

### Step 6: Commit the initial state

```bash
git add -A
git commit -m "Initialize research project with DRL"
```

This snapshot is your baseline. Every change from here is tracked and reversible.

---

## How a Research Session Works

DRL is a harness for long-running AI research sessions. You set up the infrastructure once (steps 1-6 above), then kick off sessions that can run for hours autonomously. Here is the typical flow.

### Entry point 1: Architect (broad research question)

If you have a broad research topic and need to break it into manageable pieces:

```
/drl:architect
```

The architect asks you clarifying questions about your research question, searches your indexed literature, helps you formulate hypotheses, and decomposes the project into 4-6 epics. Each epic becomes a self-contained unit: "Estimate the baseline model," "Run the IV specification," "Write the methodology section," etc.

### Entry point 2: Cook-it (single epic)

Once you have epics, run the full pipeline on one:

```
/drl:cook-it <epic-id>
```

Cook-it chains five phases with enforcement gates:

1. **Spec** -- Socratic refinement of the research question, hypotheses, and identification strategy
2. **Plan** -- Methodology design, variable operationalization, analysis plan with acceptance criteria
3. **Work** -- Execute: run regressions, generate tables/figures, draft paper sections
4. **Review** -- Multi-agent audit of methodology, statistics, writing, and reproducibility
5. **Synthesis** -- Compile the paper, verify coherence, capture lessons

Each phase has a gate. Cook-it will not advance to the next phase until the current gate passes. If a gate fails, you fix the issue and re-run.

### Entry point 3: Autonomous loop

For fully autonomous execution of multiple epics:

```bash
drl loop --epics "E1,E2,E3" --force
screen -dmS research-loop ./infinity-loop.sh
```

This generates a script that processes epics sequentially through cook-it, handling retries, dependency ordering, and memory management. It runs in a detached screen session -- you can disconnect and come back later.

After the main loop, run the polish loop for multi-model review:

```bash
drl polish --spec-file "docs/specs/my-spec.md" --meta-epic "meta-1" --force
screen -dmS research-polish ./polish-loop.sh
```

### What you do during a session

For interactive sessions (`/drl:architect`, `/drl:cook-it`):
- Answer the Socratic questions at each gate
- Approve or reject the research specification
- Review and approve the methodology plan
- Triage review findings (Critical/Major/Minor)

For autonomous sessions (`drl loop`):
- Monitor with `drl watch`
- Check progress with `bd stats`
- Review outputs when notified

### What you get at the end

After a complete pipeline run:

- **A compiled LaTeX paper** in `paper/main.tex` with all sections drafted
- **Regression tables** in `paper/outputs/tables/` (machine-generated, reproducible)
- **Figures** in `paper/outputs/figures/`
- **A decision log** in `docs/decisions/` documenting every methodological choice
- **A reproducibility manifest** capturing data checksums, package versions, random seeds
- **Captured lessons** in the memory system for future sessions

---

## The Long-Duration Harness

Unlike a one-shot script, DRL is designed for research campaigns that span days or weeks across many sessions. The harness components that make this work:

**Beads** tracks research progress across sessions. When a session ends mid-pipeline, the next session picks up where it left off by reading epic notes and task status.

**Decision logging** creates a permanent record of every methodological choice. When you return to the project weeks later, or when a reviewer asks "why fixed effects instead of random effects?", the answer is in `docs/decisions/`.

**The memory system** captures lessons learned during analysis -- statistical pitfalls, data quality issues, specification choices that worked or failed. Future sessions load these automatically, preventing the same mistakes.

**Phase gates** enforce quality. You cannot skip from planning to synthesis. Each phase must pass its gate, and the gate conditions are checked mechanically.

**The knowledge base** (97 docs covering econometrics, causal inference, identification, robustness, writing) is always available to agents. They consult it during analysis and review, not from memory, but by reading the actual documents each time.

---

## Quick Reference

| Task | Command |
|------|---------|
| Initialize project | `drl setup` |
| Index literature | `drl index` |
| Customize for your field | `/drl:flavor` |
| Decompose research question | `/drl:architect` |
| Run full pipeline on one epic | `/drl:cook-it <epic-id>` |
| Run autonomous loop | `drl loop --force && screen -dmS loop ./infinity-loop.sh` |
| Search knowledge docs | `drl knowledge "query"` |
| Search past lessons | `drl search "query"` |
| Log a decision | `/drl:decision` |
| Check project health | `drl doctor` |
| Check progress | `bd stats` |

---

## Next Steps

- [README.md](README.md) -- System overview and architecture
- [WORKFLOW.md](WORKFLOW.md) -- The 5-phase pipeline in detail
- [SKILLS.md](SKILLS.md) -- All skills and slash commands
- [CLI_REFERENCE.md](CLI_REFERENCE.md) -- Complete CLI reference
- [INTEGRATION.md](INTEGRATION.md) -- Hooks, beads, memory, and reproducibility internals
