"""Centralized path configuration for the DRL project."""
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = PROJECT_ROOT / "paper"
SRC_DIR = PROJECT_ROOT / "src"
OUTPUTS_DIR = PAPER_DIR / "outputs"
FIGURES_DIR = OUTPUTS_DIR / "figures"
TABLES_DIR = OUTPUTS_DIR / "tables"
DATA_DIR = PROJECT_ROOT / "data"
LITERATURE_DIR = PROJECT_ROOT / "literature"
LITERATURE_PDFS_DIR = LITERATURE_DIR / "pdfs"
LITERATURE_NOTES_DIR = LITERATURE_DIR / "notes"
DECISIONS_DIR = PROJECT_ROOT / "docs" / "decisions"
