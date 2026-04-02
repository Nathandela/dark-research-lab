# Dark Research Lab - Exploration Synthesis

*Date: 2026-04-02*

## 1. What We're Building

A **Claude Code harness for long-duration autonomous research paper production**, targeting social science research. Distributed as its own pnpm plugin (like compound-agent's `ca`), with the command namespace `/drl:*`.

The system takes a research question as input and autonomously produces a publication-ready LaTeX paper, with full methodological traceability via decision logs.

### Core Principle

> Copy the compound-agent infrastructure, then adapt the key elements from software development to academic research.

---

## 2. Architecture Decisions

| Decision | Choice | Source |
|---|---|---|
| Domain | Social sciences (economics, mixed methods, statistical analysis) | User choice |
| Duration | Variable - architect + infinity-loop + polish handles any duration | User choice |
| Autonomy | Dark factory - fully autonomous after spec, human reviews final output | User choice |
| Output | LaTeX paper with auto-generated tables/figures | User choice |
| Architect | Research question decomposition into flexible epics | User choice |
| Literature | PDF folder + RAG via compound-agent's embed system (Rust daemon + SQLite FTS5) | User choice |
| Flavors | Interactive guided session where Claude edits skills/agents directly | User choice |
| Traceability | Auto decision log + hook reminders at phase transitions | User choice |
| Binary | Own pnpm plugin, copying ca infrastructure and adapting for research | User choice |
| Phases | Flexible (architect decides epic structure) + cook-it cycle inside each epic | User choice |
| Notes | Structured channels: `researcher_notes/` (human) + `agent_notes/` (agent) | User choice |
| Onboarding | Guided setup wizard (`/drl:onboard`) | User choice |
| LaTeX | Pre-scaffolded template shipped with framework | User choice |
| Data pipeline | Framework provides src/ scaffolding, agent fills in project-specific logic | User choice |
| Namespace | `/drl:*` | User choice |

---

## 3. What We Keep from Compound-Agent

### Unchanged Infrastructure
- **ca binary core**: Memory, lessons, knowledge, search (JSONL + SQLite FTS5 + Rust embed daemon)
- **Beads (bd)**: Issue tracking with dependency graphs for epic management
- **5-phase cook-it cycle**: Spec-Dev -> Plan -> Work -> Review -> Compound
- **Phase gates + guard hooks**: PreToolUse blocks edits if skill not read
- **Infinity loop**: `ca loop` processes beads epics autonomously in sequence
- **Hook system**: SessionStart prime, PreCompact reload, UserPromptSubmit patterns, PostToolUseFailure tracking, phase guard
- **Memory/lessons JSONL**: Git-tracked, conflict-free, auto-injected at session start

### Reused Patterns
- **Skill-as-instruction-file**: Commands are thin wrappers -> Read SKILL.md (survives compaction)
- **Parallel subagent decomposition**: Architect spawns 6+ agents via Task tool, synthesizes findings
- **Advisory fleet**: External model CLIs evaluate from different lenses
- **Improvement loop**: Iterative `improve/*.md` programs for polish cycles

---

## 4. What Changes

### Skills (rewrite for research context)

| Compound-Agent Skill | Dark Research Lab Equivalent |
|---|---|
| `spec-dev` (feature specification) | `research-spec` (research question, hypotheses, methodology outline) |
| `plan` (implementation plan) | `research-plan` (analysis plan, data requirements, statistical approach) |
| `work` (code implementation) | `research-work` (literature analysis, data processing, statistical analysis, writing) |
| `review` (code review) | `methodology-review` (statistical validity, logical consistency, citation accuracy) |
| `compound` (lesson extraction) | `synthesis` (cross-section coherence, contribution clarity, findings consolidation) |
| `architect` (system decomposition) | `research-architect` (research question decomposition into epics) |
| `get-a-phd` (deep research) | `lit-review` (systematic literature review with PDF RAG) |

### Agents (replace code-focused with research-focused)

| Compound-Agent Agent | Dark Research Lab Equivalent |
|---|---|
| `implementer` | `analyst` (runs statistical analysis, generates tables/figures) |
| `test-writer` | `robustness-checker` (designs robustness checks, alternative specifications) |
| `security-reviewer` | `methodology-reviewer` (checks statistical validity, assumption violations) |
| `architecture-reviewer` | `coherence-reviewer` (checks paper structure, argument flow, cross-references) |
| `runtime-verifier` | `reproducibility-verifier` (checks that results can be reproduced from data + code) |
| `research-specialist` | `literature-analyst` (searches embedded PDFs, synthesizes findings) |
| `lint-classifier` | `citation-checker` (validates references, checks for missing citations) |
| `doc-gardener` | `writing-quality-reviewer` (prose quality, academic voice, clarity) |

### New Commands

| Command | Purpose |
|---|---|
| `/drl:onboard` | Guided setup wizard for new researchers |
| `/drl:flavor` | Interactive customization of skills/agents for researcher's field |
| `/drl:cook-it` | Full research cycle (adapted from compound cook-it) |
| `/drl:architect` | Research question decomposition |
| `/drl:lit-review` | Systematic literature review using embedded PDFs |
| `/drl:decision` | Manually record a methodological decision |
| `/drl:compile` | Generate all outputs + compile LaTeX paper |
| `/drl:status` | Research progress overview across all epics |

### New Folder Structure

```
project-root/
├── .claude/
│   ├── agents/drl/              # Research-focused agent definitions
│   ├── commands/drl/            # /drl:* slash commands
│   ├── skills/drl/              # Research phase skills
│   │   ├── agents/              # Agent role skills
│   │   └── references/          # Supplemental skill docs
│   ├── lessons/index.jsonl      # Memory (from ca)
│   ├── settings.json            # Hooks
│   └── CLAUDE.md                # Project instructions
├── .beads/                      # Issue tracking (from ca)
├── literature/                  # NEW: PDF folder for RAG
│   ├── pdfs/                    # Drop research papers here
│   └── notes/                   # Auto-generated paper summaries
├── docs/
│   ├── researcher_notes/        # NEW: Human scratch input
│   ├── agent_notes/             # NEW: Agent structured output
│   ├── decisions/               # NEW: Methodology decision records
│   ├── specs/                   # Research specifications
│   └── drl/                     # Framework documentation
├── paper/                       # NEW: LaTeX paper (pre-scaffolded)
│   ├── main.tex
│   ├── sections/
│   ├── outputs/
│   │   ├── figures/
│   │   └── tables/
│   ├── Ref.bib
│   └── compile.sh
├── src/                         # NEW: Analysis code scaffolding
│   ├── config.py                # Output paths, constants
│   ├── data/                    # Loaders, cleaners
│   ├── analysis/                # Descriptive, econometric, robustness
│   ├── visualization/           # Plots, charts
│   └── orchestrators/           # Pipeline entry points
├── scripts/                     # Build/compile scripts
├── tests/                       # Test scaffolding
├── AGENTS.md                    # Machine-readable agent instructions
└── README.md
```

---

## 5. New Systems

### 5.1 Methodology Decision Log

**Trigger**: Automatic during work phases + hook reminders at phase transitions.

**Format** (`docs/decisions/NNNN-<slug>.md`):
```markdown
---
id: NNNN
date: YYYY-MM-DD
phase: <epic-name>/<cook-it-phase>
type: <variable-selection|model-specification|robustness-strategy|data-treatment|scope-decision>
status: <accepted|superseded|rejected>
---

# Decision: <title>

## Context
What prompted this decision.

## Decision
What was decided.

## Alternatives Considered
- Alternative A: why rejected
- Alternative B: why rejected

## Rationale
Why this choice, with supporting literature references.

## Consequences
What this means for downstream analysis.

## Evidence
Link to specific analysis outputs that validate this decision.
```

**Hook integration**: A `PreToolUse` or phase-transition hook injects a reminder:
> "Remember to log any methodological decisions you're making in docs/decisions/"

### 5.2 Literature RAG Pipeline

**Flow**:
1. Researcher drops PDFs in `literature/pdfs/`
2. `drl index` (or hook on session start) processes new PDFs:
   - Extract text (via Python: `pymupdf` or `pdfplumber`)
   - Chunk into passages
   - Embed via `ca-embed` (Rust ONNX daemon, nomic-embed-text-v1.5)
   - Store in SQLite FTS5 + vector index
3. During work phases, agent uses `ca knowledge "query"` to search literature
4. Agent writes structured summaries to `literature/notes/<paper-slug>.md`

### 5.3 Flavor System

**Flow** (`/drl:flavor`):
1. Claude asks researcher about their field, methodology norms, journal targets, citation style
2. Claude searches web/literature for field-specific conventions
3. Claude directly edits skill files in `.claude/skills/drl/` to:
   - Adjust methodology vocabulary
   - Change evidence standards
   - Modify robustness expectations
   - Update citation style preferences
   - Adjust writing tone/formality
4. Changes are git-tracked, reversible via `git diff`

### 5.4 Onboarding Wizard

**Flow** (`/drl:onboard`):
1. Explain the framework structure (what's where, how it works)
2. Ask: What's your research question?
3. Ask: What data do you have / need?
4. Suggest running `/drl:flavor` to customize for their field
5. Guide them to drop literature PDFs
6. Suggest running `/drl:architect` to decompose the research question
7. Explain how to monitor progress and review outputs

### 5.5 Pre-Scaffolded LaTeX Template

Based on the FinancialReturnsPressScores pattern:
- `main.tex` with standard academic paper structure
- `sections/` directory with stubs for each section
- `outputs/figures/` and `outputs/tables/` for auto-generated content
- `Ref.bib` for bibliography
- `compile.sh` for 3-pass pdflatex + bibtex
- Customizable preamble (fonts, colors, packages)

### 5.6 Source Code Scaffolding

Based on the FinancialReturnsPressScores pattern:
- `src/config.py` - centralized paths and constants
- `src/data/loaders.py` - data loading stubs
- `src/data/cleaners.py` - data cleaning stubs
- `src/analysis/descriptive.py` - descriptive statistics
- `src/analysis/econometrics.py` - regression analysis
- `src/analysis/robustness.py` - robustness checks
- `src/visualization/plots.py` - visualization
- `src/orchestrators/` - pipeline entry points
- `tests/` - test structure matching src/

---

## 6. Research-Adapted Cook-It Cycle

The cook-it cycle remains 5 phases, but each phase's skill is rewritten:

### Phase 1: Research Spec (`/drl:spec`)
- Define research question precisely
- State hypotheses (null + alternative)
- Outline expected methodology
- Identify data requirements
- Literature gap analysis (using RAG)
- **Gate**: Research question + hypotheses approved

### Phase 2: Research Plan (`/drl:plan`)
- Detail statistical methodology
- Define variable operationalization
- Specify model equations
- Plan robustness checks
- Map: hypothesis -> analysis -> expected output -> paper section
- **Gate**: Methodology plan approved

### Phase 3: Research Work (`/drl:work`)
- Execute analysis plan
- Generate tables and figures
- Write paper sections
- Auto-log decisions to `docs/decisions/`
- Agent writes progress notes to `agent_notes/`
- **Gate**: All planned analyses complete

### Phase 4: Methodology Review (`/drl:review`)
- Statistical validity check (assumptions, model fit, power)
- Logical consistency (do conclusions follow from results?)
- Citation accuracy (are claims properly sourced?)
- Reproducibility check (can outputs be regenerated?)
- Writing quality review
- **Gate**: All review criteria pass

### Phase 5: Synthesis (`/drl:compound`)
- Cross-section coherence check
- Contribution clarity assessment
- Decision log review (are all decisions justified?)
- Extract lessons learned for memory system
- Final LaTeX compilation
- **Gate**: Paper compiles, all references resolve, all figures/tables present

---

## 7. Research-Adapted Architect

The architect skill is the most critical adaptation. Instead of decomposing a system into bounded contexts, it decomposes a research question into epics:

### Socratic Phase (adapted)
- Search existing literature (via RAG) and memory
- Build domain glossary (key terms, variables, constructs)
- Map the research landscape (existing findings, gaps)
- Identify methodological options and their trade-offs
- **Gate**: Understanding is complete

### Decomposition Phase (adapted)
Spawn parallel subagents:
1. **Literature mapper**: Identify key papers, theories, debates
2. **Methodology analyst**: Evaluate statistical approaches, identify assumptions
3. **Data requirements analyst**: Map variables to data sources, assess availability
4. **Scope sizer**: Ensure each epic is completable in one cook-it cycle
5. **Traceability designer**: Map hypotheses -> analyses -> evidence requirements
6. **Risk analyst**: Identify methodological risks, data quality concerns

### Materialization Phase
Create beads epics with dependencies:
- Epic 1: Literature Review (no dependencies)
- Epic 2: Data Preparation (depends on: lit review for variable definitions)
- Epic 3: Descriptive Analysis (depends on: data prep)
- Epic 4: Main Analysis (depends on: descriptive)
- Epic 5: Robustness Checks (depends on: main analysis)
- Epic 6: Paper Synthesis (depends on: all above)
- Epic IV: Integration Verification (depends on: all domain epics)

---

## 8. Landscape Context

### Key Finding
No existing tool does what we're building. The closest competitors (AI-Scientist-v2, AI-Researcher, EvoScientist, Kosmos) are all ML/STEM focused and none enforces methodological traceability.

### Our Differentiators
1. **Social science focus** - No competitor targets social sciences
2. **Methodological traceability** - Decision logs as first-class citizens
3. **Claude Code native** - Leverages hooks, skills, agents, compaction survival
4. **Dark factory autonomy** - End-to-end autonomous after spec
5. **Flavor system** - Researcher can tilt the entire harness to their field
6. **Compound-agent proven patterns** - Built on battle-tested infrastructure

### What We Borrow
- From **Kosmos**: World model pattern for shared state, validation framework
- From **EvoScientist**: Persistent memory split (ideation + experimentation)
- From **AI-Scientist-v2**: Novelty checking against existing literature
- From **PaperQA2**: RAG approach for scientific documents (we implement our own)
- From **PROV-AGENT**: W3C PROV-inspired provenance tracking concepts
- From **FinancialReturnsPressScores**: LaTeX structure, orchestrator pattern, TDD, src/ layout

---

## 9. Distribution Model

Unlike compound-agent (pnpm), the dark research lab ships as a **PyPI package** with Go binary inside platform-specific wheels (same pattern as ruff/uv):

```
drl/
├── go/                    # Go binary (adapted from ca)
│   ├── cmd/drl/main.go    # CLI entrypoint
│   └── internal/          # Core modules (adapted from ca)
│       ├── setup/templates/  # All embedded templates
│       └── ...
├── python/                # PyPI packaging wrapper
│   ├── pyproject.toml     # [project.scripts] drl = "drl:main"
│   ├── drl/__init__.py
│   └── drl/__main__.py    # Finds and executes Go binary
├── scripts/
│   └── build.py           # Cross-compile Go + package into wheels
└── .goreleaser.yaml       # GOOS/GOARCH matrix
```

Install: `uv pip install drl` (or `pip install drl`)

Rationale: researchers have Python, not Node.js. PyPI is the natural distribution channel for research tooling.

`drl setup` installs templates into any repo:
- `.claude/` (agents, commands, skills, hooks)
- `paper/` (LaTeX template)
- `src/` (analysis scaffolding)
- `docs/` (folder structure)
- `literature/` (PDF folder)
- `AGENTS.md`

---

## 10. Resolved Open Questions

| Question | Decision |
|---|---|
| Go binary | **Fork ca into 'drl' binary**. Full copy, independent evolution, clean separation. |
| Collaboration | **Single researcher only**. Simplify. Add collaboration later if needed. |
| External models | **Keep full multi-model advisory fleet** (Gemini, Codex). Key element from ca. |
| Reproducibility | **Always auto-generate** reproducibility package (uv.lock + data manifest + run script + env spec). |

## 11. Remaining Questions (to resolve during implementation)

1. **PDF processing**: Where does PDF text extraction happen - in the Go binary or as a Python preprocessing step?
2. **LaTeX template flexibility**: One adaptable template or multiple per output type?
3. **Data source integration**: Built-in connectors or always project-specific?
4. **Citation management**: Integrate with Zotero/Mendeley, or BibTeX-only interface?
