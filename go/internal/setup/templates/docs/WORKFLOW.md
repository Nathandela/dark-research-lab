---
version: "{{VERSION}}"
last-updated: "{{DATE}}"
summary: "The DRL research pipeline: architect, cook-it orchestrator, and iteration loops"
---

# Research Workflow

DRL produces research papers through a structured pipeline. The `/drl:architect` skill decomposes research questions into epics. The `/drl:cook-it` orchestrator drives each epic through five phases with enforcement gates. After individual epics complete, the infinity loop chains multiple epics and the polish loop refines the final paper.

```
architect -> cook-it (spec-dev -> plan -> work -> review -> compound) -> iterate -> polish
```

---

## The Architect

`/drl:architect` takes a broad research question and decomposes it into manageable epics through Socratic dialogue. Each epic becomes a self-contained unit of research -- a regression specification, a robustness check, a paper section, or a data pipeline.

The architect asks clarifying questions about scope, feasibility, and methodological constraints before producing the epic breakdown. Each epic gets a beads entry: `bd create --title="..." --type=epic`.

---

## Phase 1: Spec Dev

Define the research question, hypotheses, and literature gap through Socratic dialogue.

- Ask "why" before "how" -- understand the real research need
- Search memory for prior findings, methodological constraints, decisions
- Identify the literature gap and position the contribution
- Formulate testable hypotheses with expected effect directions
- Use EARS notation for precise, verifiable requirements

**Gate:** Human-approved research question and hypotheses. The researcher must confirm the RQ before any methodology work begins.

## Phase 2: Plan

Design the methodology, operationalize variables, and plan robustness checks.

- Review spec-dev output (RQ, hypotheses, literature positioning)
- Generate an `## Acceptance Criteria` table from the EARS requirements
- Generate an `## Verification Contract` recording: research profile, touched surfaces (data sources, models, paper sections), principal risks (endogeneity, selection bias, measurement error), and required evidence (regression tables, robustness checks, diagnostic plots)
- Operationalize all variables with precise definitions and data sources
- Specify the estimation strategy and identification approach
- Plan robustness checks and sensitivity analyses
- Create beads tasks: `bd create --title="..." --type=task`
- Create Review and Compound blocking tasks (these survive compaction)

**Gate:** Epic description contains both `## Acceptance Criteria` and `## Verification Contract`. Review and Compound tasks exist.

## Phase 3: Work

Execute the research through three specialized modes.

### Analysis (`work-analysis`)

Run regressions, generate tables and figures, update the reproducibility manifest. All statistical output goes to `paper/outputs/tables/` and `paper/outputs/figures/`. Every regression is logged with its specification, sample size, and key coefficients.

### Writing (`work-writing`)

Draft paper sections in LaTeX, integrate citations, and verify compilation. The main paper file is `paper/main.tex`. Each section follows the structure established in the spec-dev phase.

### Code (`work-code`)

Build analysis pipeline scripts using TDD. Tests first, then the simplest methodology that passes. This covers data cleaning, variable construction, estimation wrappers, and table formatters.

For all modes:

- Pick tasks from `bd ready`
- Read the epic's Acceptance Criteria and Verification Contract before starting
- Commit incrementally as milestones are reached
- Verify acceptance criteria before closing each task

**Gate:** All tasks closed (`bd list --status=in_progress` returns empty).

## Phase 4: Review

Dual-mode multi-agent review with automatic detection.

### Code changes (Python)

When the epic touched analysis scripts, spawn 5 specialized reviewers: statistical correctness, data pipeline integrity, reproducibility, performance, and security.

### Paper changes (LaTeX)

When the epic touched paper sections, spawn 10 specialized reviewers covering: methodology validity, coherence, writing quality, citation accuracy, reproducibility, argumentation, statistical methods, theoretical framing, contribution clarity, and robustness.

For both modes:

- Run baseline quality gates: `{{QUALITY_GATE_TEST}}` and `{{QUALITY_GATE_LINT}}`
- Verify every Acceptance Criteria row and every Verification Contract evidence item
- Classify findings: Critical (blocks proceed) / Major / Minor / Suggestion
- Resolve all Critical and Major findings before proceeding

**Gate:** No unresolved Critical or Major findings.

## Phase 5: Compound (Synthesis)

Compile the paper, verify coherence, and extract lessons. This is what makes the system compound -- each research cycle improves the next.

- Compile `paper/main.tex` and verify all references resolve
- Check cross-section coherence (do results support the claims in the introduction?)
- Verify all tables and figures are referenced and correctly numbered
- Capture methodological lessons via `drl learn`
- Cluster emerging patterns via `drl compound`
- Update decision logs and outdated documentation

**Gate:** Paper compiles cleanly, all references resolve, `{{QUALITY_GATE_TEST}}` and `{{QUALITY_GATE_LINT}}` pass, `{{QUALITY_GATE_BUILD}}` succeeds when required, and Verification Contract evidence is satisfied.

---

## Infinity Loop

The infinity loop chains multiple epics through the pipeline sequentially. After the architect decomposes a research agenda into epics, the infinity loop runs each through cook-it in dependency order. Each completed epic's findings feed into subsequent epics as prior knowledge.

## Polish Loop

The polish loop runs a multi-model advisory fleet over the near-final paper. Multiple models read the full manuscript and provide independent critique on argumentation, methodology, prose clarity, and presentation. The researcher triages feedback and applies revisions in a final cook-it pass.

---

## Phase Gates Summary

| Phase | Gate | Verification |
|-------|------|--------------|
| Spec Dev | RQ approved | Human confirms research question and hypotheses |
| Plan | Contract ready | `bd show <epic-id>` contains `## Acceptance Criteria` and `## Verification Contract`; Review + Compound tasks exist |
| Work | Tasks complete | `bd list --status=in_progress` returns empty |
| Review | Findings clear | All Critical and Major findings resolved |
| Compound | Paper coherent | Paper compiles, all refs resolve, quality gates pass, Verification Contract evidence satisfied |

---

## Cook-it Orchestrator

`/drl:cook-it` chains all 5 phases with enforcement gates.

### Invocation

```
/drl:cook-it <epic-id>
/drl:cook-it <epic-id> from plan
```

### Phase execution protocol

For each phase, cook-it:

1. Announces progress: `[Phase N/5] PHASE_NAME`
2. Initializes state: `drl phase-check start <phase>`
3. Reads the phase skill file (non-negotiable -- never from memory)
4. Runs `drl search` with the current research goal
5. Executes the phase following skill instructions
6. Updates epic notes: `bd update <epic-id> --notes="Phase: NAME COMPLETE | Next: NEXT"`
7. Verifies the phase gate before proceeding

If any gate fails, cook-it stops. Fix the issue before proceeding.

### State tracking

Cook-it persists state in `.claude/.drl-phase-state.json`:

```bash
drl phase-check status      # See current phase state
drl phase-check clean       # Reset phase state (escape hatch)
```

## Resumption

If interrupted mid-pipeline:

1. Run `bd show <epic-id>` and read the notes for phase state
2. Re-invoke with `from <phase>` to skip completed phases
3. Cook-it picks up from the specified phase with full context

### Session close

Before completing, cook-it runs this inviolable checklist:

```bash
git status
git add <files>
bd sync
git commit -m "..."
bd sync
git push
```
