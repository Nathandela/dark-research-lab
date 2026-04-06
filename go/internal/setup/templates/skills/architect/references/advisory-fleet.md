# Advisory Fleet

> Loaded on demand. Read when referenced by SKILL.md (Gate 2, post-Spec).

## Table of Contents

1. [Overview](#overview)
2. [Advisor Roles](#advisor-roles)
3. [Execution Protocol](#execution-protocol)
4. [Prompt Template](#prompt-template)
5. [Synthesis Format](#synthesis-format)
6. [Graceful Degradation](#graceful-degradation)

---

## Overview

The advisory fleet solicits independent research design perspectives from external model CLIs before presenting a spec to the human at Gate 2. Each advisor evaluates the spec through a different lens, producing structured feedback that gets synthesized into a brief.

Advisors are **non-blocking** -- they inform the human's decision at the gate but cannot veto it. The fleet runs once (no multi-cycle iteration like the review fleet).

**Why external models**: Different model families have different training biases and blind spots. A Gemini advisor might catch generalizability concerns that Claude overlooked. A Codex advisor might flag contribution gaps from a different angle. Model diversity produces richer advisory signal than same-model subagents with different prompts.

**Execution model**: The advisory fleet runs within an interactive Claude Code session using native tool parallelism. Each advisor is a background Bash call (`run_in_background: true`) — Claude gets notified when each finishes, then reads the reports and synthesizes.

## Advisor Roles

Four evaluation lenses, each assigned to a different model when available:

| # | Lens | Focus | Default CLI | Model Flag |
|---|------|-------|-------------|------------|
| 1 | **Identification Credibility** | Is the causal strategy convincing? Are assumptions testable? Could a reviewer punch a hole in the design? Internal validity threats. | claude | `--model claude-sonnet-4-6` |
| 2 | **External Validity & Generalizability** | Does the study generalize beyond the sample? LATE vs ATE concerns? SUTVA violations? Context dependency? | gemini | (none needed) |
| 3 | **Contribution Significance** | BHH absolute + marginal contribution? Does it clear the publication bar? Is the gap manufactured or genuine? | codex | (none needed) |
| 4 | **Feasibility & Data Adequacy** | Can this be executed with available/obtainable data? Statistical power adequate? Data quality sufficient? Timeline realistic? | claude | `--model claude-opus-4-6` |

### Lens-Specific Questions

**Identification Credibility**:
- Is the identification strategy clearly named (IV, DiD, RDD, matching, selection on observables)?
- Is the key identifying assumption stated in plain language?
- What is the primary threat to the identification? Is it addressed?
- Are there testable implications of the identification assumption (pre-trends, placebo, falsification)?
- Could a reviewer argue reverse causality, omitted variable bias, or selection bias?

**External Validity & Generalizability**:
- Does the study estimate a LATE, ATE, or ATT? Is this discussed?
- Would the finding generalize to other populations, time periods, or institutional contexts?
- Are there SUTVA concerns (spillovers, general equilibrium effects)?
- Is the sample representative of the target population?
- Are the mechanisms likely to operate in other settings?

**Contribution Significance**:
- What is the absolute contribution (does this topic matter for theory/policy)?
- What is the marginal contribution (what does this add over existing literature)?
- Is the gap statement grounded in the literature or manufactured?
- Does the value-added paragraph clearly differentiate from prior work?
- Would a referee at a top-5 journal in the target field consider this novel?

**Feasibility & Data Adequacy**:
- Is the required data available, or does it need to be collected/purchased?
- Is the sample size sufficient for the proposed identification strategy?
- Are key variables measured with acceptable precision?
- Is the timeline realistic given data access and analysis complexity?
- Are there data quality risks that could undermine the analysis?

### Assignment Fallback

When fewer than 4 CLIs are available, assign multiple lenses to the same CLI:

| Available CLIs | Assignment |
|---------------|------------|
| claude + gemini + codex | claude: Identification + Feasibility, gemini: External Validity, codex: Contribution |
| claude + gemini | claude: Identification + Feasibility, gemini: External Validity + Contribution |
| claude + codex | claude: Identification + Feasibility + External Validity, codex: Contribution |
| gemini + codex | gemini: Identification + External Validity, codex: Contribution + Feasibility |
| claude only | claude: all 4 lenses in a single prompt |
| gemini only | gemini: all 4 lenses in a single prompt |
| codex only | codex: all 4 lenses in a single prompt |

When a single CLI handles multiple lenses, combine them into one call with clearly labeled sections in the prompt (e.g., "## Lens 1: Identification Credibility ... ## Lens 2: Feasibility & Data Adequacy ..."). See the [combined-lens prompt variant](#combined-lens-variant) below.

## Execution Protocol

The advisory fleet uses Claude Code's native tool parallelism — no script file needed. Each advisor is a **background Bash call** (`run_in_background: true`). Claude gets notified as each completes, then reads the reports and synthesizes.

### Step 1: Detect available CLIs

Run a single Bash call to check which CLIs are installed and healthy:

```bash
for cli in claude gemini codex; do
  if command -v "$cli" >/dev/null 2>&1 && "$cli" --version >/dev/null 2>&1; then
    echo "$cli: available"
  else
    echo "$cli: unavailable"
  fi
done
```

If none are available, skip the advisory phase entirely.

### Step 2: Write prompt files

Use the Write tool to create one prompt file per advisor lens in `/tmp/advisory/`. Each file contains the prompt template (see [Prompt Template](#prompt-template)) with the spec content appended. Write all prompt files in parallel (multiple Write tool calls in one message).

For the fallback case where one CLI handles multiple lenses, write a single combined-lens prompt file instead (see [Combined-Lens Variant](#combined-lens-variant)).

### Step 3: Spawn advisors in parallel

Launch all advisor CLIs simultaneously using **parallel Bash tool calls with `run_in_background: true`**. Send all calls in a single message so they start at the same time.

**Claude** (sonnet or opus):
```bash
claude --model claude-sonnet-4-6 \
  --dangerously-skip-permissions \
  --output-format text \
  -p "$(cat /tmp/advisory/identification-prompt.md)" \
  > /tmp/advisory/identification-report.md 2>&1
```

**Gemini**:
```bash
gemini --yolo \
  -p "$(cat /tmp/advisory/external-validity-prompt.md)" \
  > /tmp/advisory/external-validity-report.md 2>/tmp/advisory/external-validity-stderr.log
```

**Codex** (prompt via stdin, clean output via -o):
```bash
codex exec --full-auto \
  -o /tmp/advisory/contribution-report.md \
  -- - < /tmp/advisory/contribution-prompt.md 2>/dev/null
```

Each runs in background. Claude is notified as each completes — no polling or sleeping needed.

### Step 4: Read reports and synthesize

As advisors finish, read each `*-report.md` via the Read tool. Check for:
- **Empty file**: advisor crashed or timed out
- **API errors** (first 20 lines contain `rate limit`, `API_KEY`, `unauthorized`): infrastructure issue, not advisory feedback
- **Valid feedback**: everything else

Once all reports are collected, synthesize into a brief (see [Synthesis Format](#synthesis-format)).

### Step 5: Persist

Write the synthesized brief to `docs/specs/<name>-advisory-brief.md` alongside the spec. This makes the advisory signal durable for future reference.

### Key CLI Patterns

These are the same patterns validated by the review fleet (see `review-fleet.md`):

| CLI | Flags | Why |
|-----|-------|-----|
| claude | `--dangerously-skip-permissions --output-format text` | Without skip-permissions, Claude pauses for confirmations with no human. `text` mode for parseable output. Note: `2>&1` merges stderr into the report — first line may contain a harmless "no stdin data" warning; ignore it during synthesis. |
| gemini | `--yolo` | Autonomous execution (Gemini's skip-permissions equivalent). |
| codex | `exec --full-auto -o <file> -- - < <prompt>` | `-p` is `--profile` not prompt. Positional arg or stdin for prompt. `-o` for clean output (stdout has UI chrome). |

### Timeout

The Bash tool has a configurable timeout (up to 600,000ms / 10 minutes). Set the timeout on each background Bash call to 600,000ms. If an advisor exceeds this, the Bash call terminates and Claude is notified of the timeout — no hung processes.

### Combined-Lens Variant

When a single CLI handles multiple lenses (see the [Assignment Fallback](#assignment-fallback) table), write a single combined prompt file:

```markdown
You are a research design advisor reviewing a study specification.
You will evaluate it through MULTIPLE lenses. Provide separate, clearly labeled analysis for each.

## Lens 1: Identification Credibility
Focus on: Causal strategy, identifying assumptions, internal validity threats, testable implications

## Lens 2: Feasibility & Data Adequacy
Focus on: Data availability, sample size, measurement precision, timeline realism, data quality risks

## Output Format
For EACH lens, provide:
### [Lens Name] — Concerns
- **[P0/P1/P2]** ...
### [Lens Name] — Strengths
### [Lens Name] — Confidence
HIGH / MEDIUM / LOW with justification

---

## Specification
{spec content}
```

## Prompt Template

The per-lens prompt template has these design properties:

- **Structured output format**: Explicit P0/P1/P2 severity, with Detail/Risk/Suggestion per concern. This enables mechanical aggregation during synthesis.
- **Confidence signal**: Each advisor states HIGH/MEDIUM/LOW confidence. Low confidence from the Contribution Significance advisor (devil's advocate on novelty) is actually a positive signal -- it means the contribution is hard to argue against.
- **Spec-only context**: Advisors see only the spec content, not project files. This is intentional -- they evaluate the research design on its merits without being anchored by implementation details. If the spec references external files, include the relevant excerpts inline.

**Context window note**: If the spec exceeds ~4,000 tokens (large EARS table + multiple Mermaid diagrams + full variable table), consider trimming the variable operationalization table from the advisor prompts to stay within Gemini and Codex input limits. The EARS requirements and causal diagrams carry the most signal for research design review.

## Synthesis Format

After reading all advisor reports, synthesize them into a single brief. This synthesis happens in the Claude Code conversation (not in the script).

### Brief Structure

```markdown
## Advisory Fleet Brief

**Advisors consulted**: {list of lenses that produced valid feedback}
**Advisors unavailable**: {list of lenses that failed, timed out, or were unassigned}

### P0 Concerns (if any)
{Aggregated P0 concerns across all advisors, deduplicated, with source attribution}

### P1 Concerns
{Aggregated P1 concerns, deduplicated}

### P2 Concerns
{Aggregated P2 concerns, deduplicated}

### Strengths (consensus)
{Points where multiple advisors agreed the spec is strong}

### Alternative Approaches
{Any alternatives suggested by advisors, with source attribution}

### Confidence Summary
| Advisor | Confidence | Justification |
|---------|-----------|---------------|
| Identification Credibility | HIGH/MEDIUM/LOW | ... |
| External Validity & Generalizability | HIGH/MEDIUM/LOW | ... |
| Contribution Significance | HIGH/MEDIUM/LOW | ... |
| Feasibility & Data Adequacy | HIGH/MEDIUM/LOW | ... |
```

### Deduplication

When multiple advisors flag overlapping concerns:
- **Merge only when** the same component AND the same risk are named. An Identification advisor's "no pre-trend test for the DiD" and an External Validity advisor's "DiD sample is unrepresentative" are related but distinct -- list them separately with a "(related to: ...)" note.
- When genuinely the same concern: merge into one entry, note which advisors flagged it (consensus = stronger signal), use the highest severity.
- When in doubt, keep them separate. Over-merging loses nuance; slight redundancy is acceptable.

### Persistence

Write the synthesized brief to `docs/specs/<name>-advisory-brief.md` alongside the spec. This makes the advisory signal durable -- if someone later asks why a methodological decision was made, the brief provides the multi-perspective rationale that informed Gate 2.

### Presentation at Gate 2

Include the brief in the `AskUserQuestion` at Gate 2. The Gate 2 question MUST include the advisory brief so the human sees both the spec and the external perspectives in the same view.

Options to offer:
- **Approve as-is**: Proceed to Phase 3 with the spec unchanged
- **Address concerns**: Revise the spec based on advisory feedback, then re-present Gate 2
- **Re-run advisors**: Revise the spec, then re-run the fleet from the top of this protocol with a fresh temp directory. The new brief replaces the previous one.

## Graceful Degradation

The advisory fleet adds value but is not required. Handle all failure modes gracefully:

| Scenario | Behavior |
|----------|----------|
| No CLIs available | Skip advisory phase, proceed to Gate 2 with note: "Advisory fleet skipped: no external CLIs available" |
| Some CLIs unavailable | Run with available CLIs, note gaps in brief |
| All advisors time out | Log warning, proceed to Gate 2 without advisory brief |
| All advisors return errors | Log errors, proceed to Gate 2 without advisory brief |
| Only 1 advisor succeeds | Present that single perspective, note limited coverage |

The human always has final authority at Gate 2 regardless of advisory feedback.
