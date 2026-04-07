"""Tests for centralized path configuration."""
from pathlib import Path

from src.config import (
    DATA_DIR,
    DECISIONS_DIR,
    FIGURES_DIR,
    LITERATURE_DIR,
    OUTPUTS_DIR,
    PAPER_DIR,
    PROJECT_ROOT,
    SRC_DIR,
    TABLES_DIR,
)


def test_project_root_is_directory():
    """PROJECT_ROOT should point to a real directory."""
    assert PROJECT_ROOT.is_dir()


def test_paths_are_under_project_root():
    """All configured paths should be relative to PROJECT_ROOT."""
    for p in [PAPER_DIR, SRC_DIR, DATA_DIR, LITERATURE_DIR, DECISIONS_DIR]:
        assert str(p).startswith(str(PROJECT_ROOT))


def test_output_paths_under_paper():
    """Output directories should be under paper/."""
    assert str(OUTPUTS_DIR).startswith(str(PAPER_DIR))
    assert str(FIGURES_DIR).startswith(str(OUTPUTS_DIR))
    assert str(TABLES_DIR).startswith(str(OUTPUTS_DIR))
