#!/usr/bin/env bash
set -euo pipefail

# 3-pass pdflatex + bibtex compilation.
# Security: --no-shell-escape prevents arbitrary command execution.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

pdflatex --no-shell-escape -interaction=nonstopmode main.tex
bibtex main || true
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
