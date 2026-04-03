---
name: Loop Launcher
description: Reference for configuring, launching, and monitoring research iteration loops and analysis polish loops
phase: architect
---

# Loop Launcher

Reference skill for launching and monitoring autonomous research iteration pipelines. This skill is NOT auto-loaded -- it is read on-demand when launching loops.

## Authorization Gate

Before launching any loop, you MUST have authorization:
- The user explicitly asked to launch a loop, OR
- You are inside an architect workflow where the user approved the launch phase, OR
- The user started this session by invoking `/drl:architect` with loop/launch intent

If none of these apply, use `AskUserQuestion` to confirm: "This will launch an autonomous research iteration loop with full permissions. Proceed?"

**If the user declines**: Do NOT generate scripts or launch anything. Report the parameters you would have used and stop. The user can invoke `/drl:launch-loop` later.

Do NOT autonomously decide to launch loops.

## Script Generation

### Research Iteration Loop
```bash
drl loop --epics "id1,id2,id3" \
  --model "claude-opus-4-6[1m]" \
  --reviewers "claude-sonnet,claude-opus,gemini,codex" \
  --review-every 1 \
  --max-review-cycles 3 \
  --max-retries 1 \
  --force
```

### Analysis Polish Loop
```bash
drl polish --spec-file "docs/specs/your-spec.md" \
  --meta-epic "meta-epic-id" \
  --reviewers "claude-sonnet,claude-opus,gemini,codex" \
  --cycles 2 \
  --model "claude-opus-4-6[1m]" \
  --force
```

### Flags Reference -- Research Iteration Loop (`drl loop`)

| Flag | Default | Description |
|------|---------|-------------|
| `--epics` | (auto-discover) | Comma-separated epic IDs (e.g., data-cleaning, estimation, robustness) |
| `--model` | `claude-opus-4-6[1m]` | Model for analysis implementation sessions |
| `--reviewers` | (none) | Comma-separated: `claude-sonnet,claude-opus,gemini,codex` |
| `--review-every` | `0` (end-only) | Review after every N epics |
| `--max-review-cycles` | `3` | Max review/fix iterations per analysis step |
| `--max-retries` | `1` | Retries per epic on failure |
| `--review-blocking` | `false` | Fail loop if review not approved after max cycles |
| `--review-model` | `claude-opus-4-6[1m]` | Model for implementer fix sessions |
| `-o, --output` | `infinity-loop.sh` | Output script path |
| `--force` | (off) | Overwrite existing script |

### Flags Reference -- Analysis Polish Loop (`drl polish`)

| Flag | Default | Description |
|------|---------|-------------|
| `--meta-epic` | (required) | Parent meta-epic ID for traceability |
| `--spec-file` | (required) | Path to the research spec for reviewer context |
| `--cycles` | `3` | Number of polish cycles (robustness convergence iterations) |
| `--model` | `claude-opus-4-6[1m]` | Model for polish architect sessions |
| `--reviewers` | `claude-sonnet,claude-opus,gemini,codex` | Comma-separated audit fleet |
| `-o, --output` | `polish-loop.sh` | Output script path |
| `--force` | (off) | Overwrite existing script |

## Launching

Always launch in a screen session. Never run loops in the foreground.

### Single loop
```bash
LOOP_SESSION="drl-loop-$(basename "$(pwd)")"
screen -dmS "$LOOP_SESSION" bash infinity-loop.sh
mkdir -p .beads && echo "$LOOP_SESSION" > .beads/loop-session-name
```

### Chained pipeline (iteration + polish)
```bash
cat > pipeline.sh << 'SCRIPT'
#!/bin/bash
set -e
trap 'echo "[pipeline] FAILED at line $LINENO" >&2' ERR
cd "$(dirname "$0")"
bash infinity-loop.sh
bash polish-loop.sh
SCRIPT
LOOP_SESSION="drl-loop-$(basename "$(pwd)")"
screen -dmS "$LOOP_SESSION" bash pipeline.sh
mkdir -p .beads && echo "$LOOP_SESSION" > .beads/loop-session-name
```

### Screen session naming
Use readable names: `drl-loop-projectname`, `polish-loop-projectname-cycle2`. Never use hashes.

## Pre-Flight

Before launching:
1. **Verify `drl` is the Go binary**: run `drl loop --help` and confirm Cobra-style output (`Usage: drl loop [flags]`).
2. Verify `drl polish --help` succeeds (command exists).
3. Verify all epics are status=open: `bd show <id>` for each
4. Verify `claude` CLI is available and authenticated
5. Verify `bd` CLI is available
6. Sync beads: `bd dolt push`
7. Dry-run iteration loop: `LOOP_DRY_RUN=1 bash infinity-loop.sh`
8. Dry-run polish loop: `POLISH_DRY_RUN=1 bash polish-loop.sh`
9. Verify screen is available: `command -v screen`

## Monitoring

| Command | What it shows |
|---------|---------------|
| `screen -r "$(cat .beads/loop-session-name)"` | Attach to live session (Ctrl-A D to detach) |
| `drl watch` | Live trace tail from active session |
| `cat agent_logs/.loop-status.json` | Current epic and status |
| `cat agent_logs/loop-execution.jsonl` | Completed epics with durations |
| `ls agent_logs/polish-cycle-*/` | Polish cycle reports and robustness findings |
| `screen -S "$(cat .beads/loop-session-name)" -X quit` | Kill the loop |

### Robustness Convergence Monitoring
During polish loops, watch for convergence signals:
- Coefficient stability across iterations (check `agent_logs/polish-cycle-*/`)
- Decreasing number of P1/P2 findings per cycle
- Consistent results across alternative specifications

## Gotchas

### Critical

- **Always include `--dangerously-skip-permissions --permission-mode auto --verbose` in non-interactive claude invocations.** Without `--dangerously-skip-permissions`, claude hangs on permission prompts. Without `--verbose`, `--output-format stream-json` silently exits 1.

- **Always use a quoted heredoc (`<<'DELIM'`) for prompt templates containing markdown.** Triple backticks in markdown code blocks are interpreted as bash command substitution in unquoted heredocs. Use `<<'DELIM'` and inject variables with `sed` instead.

- **Prefer the local `drl` binary over `npx drl`.** Ensure the local Go build is on PATH.

- **Use comma-separated values for `--epics` and `--reviewers`.** Space-separated arguments cause parse errors.

### CLI Flags for Advisory/Review Fleet

| CLI | Non-interactive mode | Model flag |
|-----|---------------------|------------|
| `claude` | `-p "prompt"` | `--model <id>` |
| `gemini` | `-p "prompt"` | `-m <model>` |
| `codex` | `codex exec "prompt"` | (default model) |

Stdin piping works for all three: `cat file.md | claude -p "Review this"`.

### Other Gotchas
- Run `drl loop` and `drl polish` from the project root directory
- Use `--force` when regenerating scripts to overwrite existing ones
- The polish loop is a separate script -- chain via pipeline script, not `&&` in the terminal
- Do not use `claude -m sonnet` -- use `claude --model claude-sonnet-4-6`

## Common Pitfalls

- Launching loops without verifying all analysis dependencies are installed (`uv sync`)
- Not checking that data files are present before launching data-dependent epics
- Skipping pre-flight dry-runs, leading to silent failures mid-pipeline
- Not monitoring robustness convergence during polish loops
- Forgetting to sync beads before launch (`bd dolt push`)

## Quality Criteria

- Authorization confirmed before any loop launch
- All pre-flight checks passed
- Screen session launched with readable name
- Monitoring commands provided to user
- Dry-run completed without errors before live launch
- Beads synced before launch
