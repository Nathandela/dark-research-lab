# Advisory Fleet Brief -- DRL Package

*Date: 2026-04-02*

**Advisors consulted**: Security & Reliability (Claude Sonnet), Scalability & Performance (Gemini), Organizational & Delivery (Codex), Simplicity & Alternatives (Claude Sonnet)
**Advisors unavailable**: None (all 3 CLIs operational)

---

## P0 Concerns

### 1. LaTeX command injection via shell-escape
*Source: Security*

LaTeX `\write18` (shell-escape) allows arbitrary code execution. If PDF-extracted content flows into `.tex` files, a malicious PDF could execute commands.

**Mitigation**: Use `--no-shell-escape` in `compile.sh`. Sanitize any external content inserted into `.tex`.

### 2. Unbounded autonomous spend
*Source: Security*

Dark factory + infinity loop + multi-model advisory fleet can run indefinitely with no budget guard.

**Mitigation**: Require `--max-iterations` or `--max-cost` at loop launch. Surface confirmation before crossing thresholds.

### 3. Foundation epic is a global blocker
*Source: Organizational*

Epic 1 (Go binary) does too much: fork, rename, setup, template embedding, packaging. No parallelism until it's stable.

**Mitigation**: Split Epic 1 into a thin bootstrap (binary name + setup + one smoke test) and push packaging/polish later.

---

## P1 Concerns

### 4. Phase guard fails open
*Source: Security*

If the hook crashes or is bypassed, phase guard gives false assurance. Single researcher may find it adversarial.

**Mitigation**: Document as soft advisory, not hard security boundary. Consider reminder-only mode.

### 5. Flavor system can corrupt skill files
*Source: Security*

Interrupted session leaves skill files partially overwritten with no rollback.

**Mitigation**: Git commit before editing (atomic rollback via `git checkout`).

### 6. Embed daemon lifecycle undefined
*Source: Security, Scalability*

No defined start/stop, crash recovery, or health check. Silent indexing failures produce incomplete RAG.

**Mitigation**: Health check before indexing. Surface failures explicitly.

### 7. Hidden dependencies under-modeled
*Source: Organizational*

Epics 3, 4, 7, 8 all depend on stable skill contracts. Changes to phase names, file layout, or hook events cause cross-epic churn.

**Mitigation**: Define explicit contracts early for phase state, command I/O, hook events, scaffold paths.

### 8. Cognitive load too high in Epics 3 and 4
*Source: Organizational*

"6 subagents" (Epic 3) and "8 roles + 8 commands + hooks" (Epic 4) exceed 7+/-2 concept budget.

**Mitigation**: Split Epic 3 (decomposition/execution/synthesis). Split Epic 4 (commands, hooks, agents).

### 9. Sequential epic processing bottleneck
*Source: Scalability*

One-at-a-time infinity loop means throughput is bound by the longest epic. Independent epics wait unnecessarily.

**Mitigation**: Consider DAG executor for parallel independent epics (future enhancement, not MVP).

### 10. Unbounded local resource contention
*Source: Scalability*

Rust daemon + Python scripts + LaTeX + advisory CLIs all compete for CPU/memory simultaneously.

**Mitigation**: Sequential phases already isolate most work. Monitor resource usage at scale.

### 11. Approval state for W1 undefined
*Source: Security*

"Block analysis without approved research-spec" -- no defined mechanism for what "approved" means.

**Mitigation**: Use beads status field (e.g., spec bead must be status=closed before work phase).

### 12. Template deployment becomes a public API
*Source: Organizational*

Once `drl setup` writes files into repos, scaffold shape is locked. Later changes force migration.

**Mitigation**: Version the template schema. Make `drl setup --update` a first-class migration path.

---

## P2 Concerns

- **Binary distribution trust** (Security): No checksum verification. Mitigate: publish SHA256 with releases.
- **Credential management** (Security): Multi-model fleet needs API keys. Mitigate: env vars + `.gitignore` check in `drl doctor`.
- **SQLite vector degradation at corpus scale** (Scalability): Vector search may degrade at 100x. Mitigate: use ANN index, periodic optimization.
- **Synchronous PDF ingestion** (Scalability): Batch drops block queries. Mitigate: async background ingestion.
- **Advisory fleet rate limiting** (Scalability): Concurrent API calls may hit rate limits. Mitigate: concurrency control.
- **Cross-ecosystem coordination** (Organizational): Go + markdown + shell + Python + Rust spans many toolchains. Mitigate: hard ownership boundaries per language.

---

## Simplicity Advisor: Alternative Architecture

The Simplicity lens (HIGH confidence) proposed a minimal viable version:

1. **Template overlay on stock `ca`** instead of fork (no Go maintenance)
2. **FTS5-only literature search** instead of Rust ONNX daemon
3. **Single-model review** instead of multi-model fleet
4. **Config file** instead of flavor interview system
5. Keep: LaTeX + Python scaffolding, decision log

**Note**: Items 1, 2, and 3 conflict with explicit user decisions (fork binary, reuse ca-embed, keep multi-model fleet). Presented for awareness but these are settled architecture decisions.

---

## Strengths (Consensus)

- **Skill-as-instruction-file** pattern is sound (Security + Simplicity)
- **Decision log** is genuine domain value, not over-engineering (Simplicity + Organizational)
- **LaTeX + Python scaffolding** is appropriate for the domain (Simplicity + Scalability)
- **Local SQLite** avoids external DB complexity (Scalability)
- **Single-developer ownership** keeps coordination cost low (Organizational)
- **Sequential phases** prevent file I/O races (Scalability)

---

## Confidence Summary

| Advisor | Confidence | Justification |
|---------|-----------|---------------|
| Security & Reliability | MEDIUM | Phase guard enforcement and loop termination underspecified |
| Scalability & Performance | MEDIUM | Appropriate for single-actor local CLI; ambiguity around dataset size |
| Organizational & Delivery | MEDIUM | Dependencies likely understated; hidden couplings between skills/hooks/scaffold |
| Simplicity & Alternatives | HIGH | Clear over-engineering signals, but some conflict with settled user decisions |
