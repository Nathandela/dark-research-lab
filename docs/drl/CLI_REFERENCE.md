---
version: "2.6.1"
last-updated: "2026-04-03"
summary: "Complete CLI command reference for dark-research-lab"
---

# CLI Reference

All commands use `drl` (or `npx drl` if not in PATH). Global flags: `-v, --verbose` and `-q, --quiet`.

---

## Capture commands

```bash
# Capture a lesson (primary command)
drl learn "Always validate epic IDs before shell execution" \
  --trigger "Shell injection via bd show" \
  --tags "security,validation" \
  --severity high \
  --type lesson

# Capture a pattern (requires --pattern-bad and --pattern-good)
drl learn "Use execFileSync instead of execSync" \
  --type pattern \
  --pattern-bad "execSync(\`bd show \${id}\`)" \
  --pattern-good "execFileSync('bd', ['show', id])"

# Capture from trigger/insight flags
drl capture --trigger "Tests failed after refactor" --insight "Run full suite after moving files" --yes

# Detect learning triggers from input file
drl detect --input corrections.json
drl detect --input corrections.json --save --yes
```

**Types**: `lesson` (default), `solution`, `pattern`, `preference`
**Severity**: `high`, `medium`, `low`

## Retrieval commands

```bash
drl search "sqlite validation"           # Keyword search
drl search "security" --limit 5
drl list                                  # List all memory items
drl list --limit 20
drl list --invalidated                    # Show only invalidated items
drl check-plan --plan "Implement caching layer for API responses"
echo "Add caching layer" | drl check-plan # Semantic search against a plan
drl load-session                          # Load high-severity lessons
drl load-session --json
```

## Management commands

```bash
drl show <id>                             # View a specific item
drl show <id> --json
drl update <id> --insight "Updated text"  # Update item fields
drl update <id> --severity high --tags "security,input-validation"
drl delete <id>                           # Soft delete (creates tombstone)
drl delete <id1> <id2> <id3>
drl wrong <id> --reason "Incorrect"       # Mark as invalid
drl validate <id>                         # Re-enable an invalidated item
drl export                                # Export as JSON
drl export --since 2026-01-01 --tags "security"
drl import lessons-backup.jsonl           # Import from JSONL file
drl compact                               # Remove tombstones and rebuild index
drl compact --dry-run
drl compact --force
drl rebuild                               # Rebuild SQLite index from JSONL
drl rebuild --force
drl stats                                 # Show database health and statistics
drl prime                                 # Reload workflow context after compaction
```

## Setup commands

```bash
drl init                    # Initialize in current repo
drl init --skip-agents      # Skip AGENTS.md and template installation
drl init --skip-hooks       # Skip git hook installation
drl init --skip-claude      # Skip Claude Code hooks
drl init --json             # Output result as JSON
drl setup                   # Full setup (init + hooks + templates)
drl setup --update          # Regenerate templates (preserves user files)
drl setup --uninstall       # Remove compound-agent integration
drl setup --status          # Show installation status
drl setup claude            # Install Claude Code hooks only
drl setup claude --status   # Check hook status
drl setup claude --dry-run  # Preview changes without writing
drl setup claude --global   # Use global ~/.claude/ settings
drl setup claude --uninstall # Remove compound-agent hooks
drl download-model          # Download embedding model (~23MB)
drl download-model --json   # Output result as JSON
```

## Reviewer commands

```bash
drl reviewer enable gemini  # Enable Gemini as external reviewer
drl reviewer enable codex   # Enable Codex as external reviewer
drl reviewer disable gemini # Disable a reviewer
drl reviewer list           # List enabled reviewers
```

## Loop command

```bash
drl loop                    # Generate infinity loop script for autonomous processing
drl loop --epics epic-1 epic-2
drl loop --output my-loop.sh
drl loop --max-retries 5
drl loop --model claude-opus-4-6[1m]
drl loop --force            # Overwrite existing script
```

## Improve command

```bash
drl improve                           # Generate improvement loop script
drl improve --topics lint tests       # Run only specific topics
drl improve --max-iters 3             # Max iterations per topic (default: 5)
drl improve --time-budget 3600        # Total time budget in seconds (0=unlimited)
drl improve --model claude-sonnet-4-6 # Choose model
drl improve --output my-improve.sh    # Custom output path
drl improve --force                   # Overwrite existing script
drl improve --dry-run                 # Validate and print plan without generating
drl improve init                      # Scaffold example improve/*.md program file
```

## Watch command

```bash
drl watch                             # Tail live trace from latest loop session
drl watch --epic <id>                 # Watch a specific epic trace
drl watch --improve                   # Watch improvement loop traces
drl watch --no-follow                 # Print existing trace and exit
```

## Health, audit, and verification commands

```bash
drl about                    # Show version, animation, and recent changelog
drl doctor                  # Check external dependencies and project health
drl audit                   # Run pattern, rule, and lesson quality checks
drl rules check             # Check codebase against .claude/rules.json
drl test-summary            # Run tests and output compact pass/fail summary
drl verify-gates <epic-id>  # Verify workflow gates before epic closure
drl phase-check init <epic-id>
drl phase-check status
drl phase-check start <phase>
drl phase-check gate <gate-name>   # post-plan, gate-3, gate-4, final
drl phase-check clean
```

## Compound command

```bash
drl compound                # Synthesize cross-cutting patterns from accumulated lessons
```
