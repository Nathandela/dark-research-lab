---
version: "{{VERSION}}"
last-updated: "{{DATE}}"
summary: "Overview and getting started guide for dark-research-lab"
---

# Dark Research Lab

An autonomous research pipeline for social science. You define the research question and theoretical motivation, DRL helps you spec the methodology, then executes the analysis, writes the paper, reviews it, and synthesizes lessons -- end to end. You bring the "what and why"; DRL handles the "how".

DRL is not a statistical package. It is a compound-agent system that orchestrates 27 specialized agents through a 5-phase research cycle, producing publication-quality LaTeX papers with full methodological traceability.

---

## Who is it for?

Social science researchers who use Python for empirical analysis and target journal-quality papers. DRL assumes familiarity with research design (hypotheses, identification strategies, robustness checks) but handles the mechanical execution: data pipelines, econometric code, table/figure generation, LaTeX compilation, and internal review.

---

## Quick start

```bash
# Install DRL and beads
uv tool install dark-research-lab
npm install -g beads

# Create and scaffold a research project
mkdir my-paper && cd my-paper && git init
drl setup

# Add your data (keep originals safe elsewhere) and literature
cp ~/data/*.csv data/input/
cp ~/papers/*.pdf literature/pdfs/
drl index

# Customize for your field (labor economics, political science, etc.)
/drl:flavor

# Two entry points:
/drl:architect    # Decompose a broad topic into research epics
/drl:cook-it      # Run the full 5-phase pipeline on a single epic
```

---

## The research pipeline

Every project follows five phases. The `/drl:cook-it` orchestrator chains them with enforcement gates.

1. **Spec** -- Define the research question, hypotheses, and literature gap through Socratic dialogue. Produces a formal research specification with EARS-notation requirements.

2. **Plan** -- Design the methodology: operationalize variables, select estimators, plan robustness checks. Decomposes the spec into concrete analysis tasks with acceptance criteria.

3. **Work** -- Run the analysis, write paper sections, generate tables and figures. Three execution modes (code, writing, analysis) with agent teams working under TDD.

4. **Review** -- Dual-mode review fleet: code quality reviewers check implementation correctness, methodology/writing reviewers check statistical validity, identification threats, and prose quality.

5. **Synthesis** -- Compile the paper, verify cross-section coherence, extract methodological lessons for future projects.

---

## What ships

| Category | Count | Description |
|----------|-------|-------------|
| Agents | 27 | Specialized roles (econometrician, reviewer, writer, etc.) |
| Skills | 22 | Phase instructions and agent role knowledge |
| Commands | 23 | Slash commands for every workflow step |
| Knowledge docs | 16 | PhD-level references: social science methodology (5) + Python architecture (11) |
| LaTeX scaffold | 7 sections | Paper template with compilation script |
| Python skeleton | 6 modules | Analysis, data, visualization, orchestration |

---

## Directory structure

After `drl setup`, your project gets:

```
.claude/
  CLAUDE.md                    # Project instructions (always loaded)
  settings.json                # Claude Code hooks
  plugin.json                  # Plugin manifest
  agents/drl/                  # 27 subagent definitions
  commands/drl/                # 23 slash commands
  skills/drl/                  # 22 phase + agent role skills
paper/
  main.tex                     # Main paper file
  sections/                    # intro, literature, methodology, data, results, robustness, conclusion
  outputs/tables/              # Generated LaTeX tables
  outputs/figures/             # Generated figures
  Ref.bib                      # Bibliography
  compile.sh                   # Compilation script
src/
  analysis/                    # descriptive, econometrics, robustness
  data/                        # loaders, cleaners
  visualization/               # plots
  literature/                  # extraction utilities
  orchestrators/               # reproducibility pipeline
data/
  input/                       # Raw data
  output/                      # Processed data
docs/
  decisions/                   # ADR-style methodology decision log
  researcher_notes/            # Working notes
  agent_notes/                 # Agent working memory
literature/
  pdfs/                        # Source papers
  notes/                       # Literature notes
docs/drl/
  research/                    # 97 PhD-level knowledge documents
tests/                         # Test suite
```

---

## Quick reference

| Task | Command |
|------|---------|
| Full autonomous pipeline | `/drl:cook-it <epic-id>` |
| Decompose broad topic into epics | `/drl:architect` |
| Define research spec (Socratic) | `/drl:spec-dev` |
| Plan methodology and tasks | `/drl:plan` |
| Execute analysis and writing | `/drl:work` |
| Run review fleet | `/drl:review` |
| Synthesize and compile | `/drl:compound` |
| Customize research flavor | `/drl:flavor` |
| Literature review | `/drl:lit-review` |
| Search knowledge docs | `drl knowledge "query"` |
| Health check | `drl doctor` |

---

## Further reading

- [ONBOARDING.md](ONBOARDING.md) -- **Start here.** Full setup walkthrough: install, data, literature, first session
- [WORKFLOW.md](WORKFLOW.md) -- The 5-phase research pipeline in detail
- [SKILLS.md](SKILLS.md) -- Phase skills and agent role skills reference
- [CLI_REFERENCE.md](CLI_REFERENCE.md) -- Complete CLI command reference
- [INTEGRATION.md](INTEGRATION.md) -- Hooks, beads, memory, and reproducibility internals
