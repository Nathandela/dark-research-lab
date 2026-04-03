#!/usr/bin/env bash
set -euo pipefail

# 3-pass pdflatex + bibtex compilation.
# Security: --no-shell-escape prevents arbitrary command execution.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

pdflatex --no-shell-escape -interaction=nonstopmode main.tex

# Run bibtex with explicit error reporting instead of silently swallowing failures.
# Bibtex exit codes: 0=success, 1=warnings, 2=errors.
# Non-zero is reported but non-fatal since PDFs still generate without bib.
bibtex_rc=0
bibtex main || bibtex_rc=$?
if [ "$bibtex_rc" -ge 2 ]; then
    echo "Error: bibtex exited with code $bibtex_rc -- check main.blg for details" >&2
elif [ "$bibtex_rc" -eq 1 ]; then
    echo "Warning: bibtex exited with code 1 (warnings) -- check main.blg for details" >&2
fi

pdflatex --no-shell-escape -interaction=nonstopmode main.tex
pdflatex --no-shell-escape -interaction=nonstopmode main.tex

# Generate reproducibility manifest
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
if command -v uv &>/dev/null; then
    (cd "$REPO_ROOT" && uv run python -m src.orchestrators.repro --output-dir "$SCRIPT_DIR") || echo "Warning: repro manifest generation failed" >&2
elif command -v python3 &>/dev/null; then
    PYTHONPATH="$REPO_ROOT" python3 -m src.orchestrators.repro --output-dir "$SCRIPT_DIR" || echo "Warning: repro manifest generation failed" >&2
fi

echo "Compilation complete: main.pdf"
