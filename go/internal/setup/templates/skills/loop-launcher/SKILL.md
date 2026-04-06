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
1. **Verify `drl` is the Go binary**: run `drl loop --help` and confirm it shows Cobra-style output (`Usage: drl loop [flags]`). If the command is not found, ensure the local Go build at `go/dist/drl` is on PATH.
2. Verify `drl polish --help` succeeds (command exists).
3. Verify all epics are status=open: `bd show <id>` for each
4. Verify `claude` CLI is available and authenticated
5. Verify `bd` CLI is available
6. Sync beads: `bd dolt push`
7. Dry-run iteration loop: `LOOP_DRY_RUN=1 bash infinity-loop.sh`
8. Dry-run polish loop: `POLISH_DRY_RUN=1 bash polish-loop.sh`
9. Verify screen is available: `command -v screen`

Full pre-flight checklist with monitoring protocol: `architect/references/infinity-loop/pre-flight.md`.

## Monitoring

### Quick Reference

| Command | What it shows |
|---------|---------------|
| `screen -r "$(cat .beads/loop-session-name)"` | Attach to live session (Ctrl-A D to detach) |
| `drl watch` | Live trace tail from active session |
| `cat agent_logs/.loop-status.json` | Current epic and status |
| `cat agent_logs/loop-execution.jsonl` | Completed epics with durations |
| `ls agent_logs/polish-cycle-*/` | Polish cycle reports and robustness findings |
| `screen -S "$(cat .beads/loop-session-name)" -X quit` | Kill the loop |

### Post-Launch Verification

After launching a loop in screen, verify it started by running a background Bash command (`run_in_background: true`):

```bash
# Check 1: status file
sleep 60 && cat agent_logs/.loop-status.json 2>/dev/null || echo "No status file yet"
# Check 2: screen session
screen -ls 2>/dev/null | grep "$(cat .beads/loop-session-name 2>/dev/null || echo drl-loop)" || echo "No screen session found"
```

When the result comes back: if `.loop-status.json` shows `"status":"running"` and screen lists the session, report success to the user. If not, check for crash details or missing screen session and report the issue.

### Health Check Protocol

When the user asks about loop progress, follow this protocol to build a structured overview.

**Step 1 -- Gather data** (use parallel subagents for speed):
- Read `agent_logs/.loop-status.json` -- current epic, attempt number, status
- Read `agent_logs/loop-execution.jsonl` -- all completed epics with result, duration
- Run `bd show <epic-id>` for each epic to get titles and statuses
- Run `git log --oneline -5` to see recent commit activity
- For polish loops: also read `agent_logs/.polish-status.json` and list `agent_logs/polish-cycle-*/`

**Step 2 -- Detect stalls**:
- If `.loop-status.json` shows `"status":"running"`, check when it was last modified:
  - macOS: `stat -f '%m' agent_logs/.loop-status.json`
  - Linux: `stat -c '%Y' agent_logs/.loop-status.json`
- Calculate the delta: `DELTA=$(( $(date +%s) - $(stat -f '%m' agent_logs/.loop-status.json) ))` (macOS) or `DELTA=$(( $(date +%s) - $(stat -c '%Y' agent_logs/.loop-status.json) ))` (Linux). If `$DELTA > 300`, proceed with stall check below.
- If last modified > 5 minutes ago: read the last 20 lines of the active trace (`tail -20 "agent_logs/$(readlink agent_logs/.latest)"`), wait 15 seconds, read again. If output is identical, flag as potentially stalled.
- If status is `"crashed"`: report crash details (exit code, line number, timestamp) immediately.
- Verify screen session is alive: `screen -ls | grep "$(cat .beads/loop-session-name)"`

**Step 3 -- Build the overview**:

Present a structured report like this:

```
[one-line summary: "X of Y epics done, currently working on Z"]

| # | Epic | Status | Duration |
|---|------|--------|----------|
| 1 | Epic title from beads | Closed | ~8 min |
| 2 | Another epic | Running | started HH:MM UTC |
| 3 | Upcoming epic | Open | -- |

[total runtime, average per completed epic, ETA for remaining epics]
[any anomalies: failures, retries, human_required, stalls]
```

**Note on ETA**: The loop does not persist a target epic count. To calculate "X of Y", query `bd list --type=epic --status=open` for remaining epics and count completed entries in `loop-execution.jsonl`. ETAs are rough estimates -- epic duration varies with complexity, retries, and memory pressure.

- **Closed epics**: duration from `loop-execution.jsonl` (convert seconds to human-readable)
- **Running epic**: "started HH:MM UTC" from `.loop-status.json` timestamp
- **Open epics**: "--"
- **Pace**: total elapsed, average per epic, rough ETA for remaining
- **Anomalies**: flag failures, retries (attempt > 1), human_required markers, or stalled sessions

### Log File Map

| Path | Content | When to read |
|------|---------|-------------|
| `agent_logs/.loop-status.json` | Current epic, attempt, status | Always -- primary status |
| `agent_logs/loop-execution.jsonl` | Completed epics with result, duration | Always -- progress history |
| `agent_logs/.latest` | Symlink to active trace file | Stall detection |
| `agent_logs/trace_<id>-<ts>.jsonl` | Raw stream-json per session | Deep debugging only |
| `agent_logs/loop_<id>-<ts>.log` | Extracted assistant text per session | Investigating a specific epic |
| `agent_logs/memory_<id>-<ts>.log` | Memory watchdog readings | Suspecting OOM |
| `agent_logs/.polish-status.json` | Polish loop cycle/status | During polish loops |
| `agent_logs/polish-cycle-<N>/` | Per-cycle robustness findings and reports | Polish loop review |

### Robustness Convergence Monitoring
During polish loops, watch for convergence signals:
- Coefficient stability across iterations (check `agent_logs/polish-cycle-*/`)
- Decreasing number of P1/P2 findings per cycle
- Consistent results across alternative specifications

## Gotchas

### Critical

- **Always include `--dangerously-skip-permissions --permission-mode auto --verbose` in non-interactive claude invocations.** Without `--dangerously-skip-permissions`, claude hangs on permission prompts. Without `--verbose`, `--output-format stream-json` silently exits 1. The `drl loop` generator includes all three -- if a generated script is missing them, the binary is stale.

- **Always use a quoted heredoc (`<<'DELIM'`) for prompt templates containing markdown.** Triple backticks in markdown code blocks are interpreted as bash command substitution in unquoted heredocs. Use `<<'DELIM'` and inject variables with `sed` instead.

- **Ensure the `drl` binary on PATH is the current Go build.** The polish loop generates inner loop scripts via `drl loop`. If the binary is stale, generated scripts may lack critical flags (`--dangerously-skip-permissions`, `--verbose`) or use unquoted heredocs.

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
- Do not use `gemini --print`, `codex --print`, or `claude --print` -- wrong flags
- Do not use `claude -m sonnet` -- use `claude --model claude-sonnet-4-6`

## Common Pitfalls

- Launching loops without verifying all analysis dependencies are installed (`uv sync`)
- Not checking that data files are present before launching data-dependent epics
- Skipping pre-flight dry-runs, leading to silent failures mid-pipeline
- Not monitoring robustness convergence during polish loops
- Forgetting to sync beads before launch (`bd dolt push`)

## Windows Users

All sections above assume Unix/macOS. Windows users should read the `references/windows/` directory:

- **`windows-wsl2.md`** -- Recommended path. Run loops unmodified inside WSL2 with tmux for session management. Covers both infinity and polish loops.
- **`infinity-loop.ps1`** -- Native PowerShell reference template. Static translation of the bash infinity loop for users who cannot use WSL2. Runs in foreground only (no screen/tmux equivalent). See the Known Limitations header in the file for gaps.

The `references/windows/` directory is ONLY relevant for Windows users. Unix/macOS users can ignore it entirely.

## Quality Criteria

- Authorization confirmed before any loop launch
- All pre-flight checks passed
- Screen session launched with readable name
- Monitoring commands provided to user
- Dry-run completed without errors before live launch
- Beads synced before launch
