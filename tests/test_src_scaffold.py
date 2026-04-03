"""Tests for src/ Python analysis scaffolding (Epic 3)."""
import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SRC_DIR = REPO_ROOT / "src"


class TestSrcDirectoryStructure:
    def test_src_dir_exists(self):
        assert SRC_DIR.is_dir()

    def test_src_init_exists(self):
        assert (SRC_DIR / "__init__.py").is_file()

    def test_config_exists(self):
        assert (SRC_DIR / "config.py").is_file()

    def test_data_dir(self):
        data_dir = SRC_DIR / "data"
        assert (data_dir / "__init__.py").is_file()
        assert (data_dir / "loaders.py").is_file()
        assert (data_dir / "cleaners.py").is_file()

    def test_analysis_dir(self):
        analysis_dir = SRC_DIR / "analysis"
        assert (analysis_dir / "__init__.py").is_file()
        assert (analysis_dir / "descriptive.py").is_file()
        assert (analysis_dir / "econometrics.py").is_file()
        assert (analysis_dir / "robustness.py").is_file()

    def test_visualization_dir(self):
        viz_dir = SRC_DIR / "visualization"
        assert (viz_dir / "__init__.py").is_file()
        assert (viz_dir / "plots.py").is_file()

    def test_orchestrators_dir(self):
        assert (SRC_DIR / "orchestrators" / "__init__.py").is_file()


MODULES = [
    "src",
    "src.config",
    "src.data",
    "src.data.loaders",
    "src.data.cleaners",
    "src.analysis",
    "src.analysis.descriptive",
    "src.analysis.econometrics",
    "src.analysis.robustness",
    "src.visualization",
    "src.visualization.plots",
    "src.orchestrators",
]


class TestPythonImports:
    @pytest.mark.parametrize("module", MODULES)
    def test_module_imports(self, module):
        # Clear any cached imports to test fresh
        for key in list(sys.modules.keys()):
            if key.startswith("src"):
                del sys.modules[key]
        mod = importlib.import_module(module)
        assert mod is not None


class TestConfigPaths:
    def test_defines_project_root(self):
        from src.config import PROJECT_ROOT
        assert isinstance(PROJECT_ROOT, Path)

    def test_defines_paper_dir(self):
        from src.config import PAPER_DIR
        assert isinstance(PAPER_DIR, Path)
        assert PAPER_DIR.name == "paper"

    def test_defines_src_dir(self):
        from src.config import SRC_DIR
        assert isinstance(SRC_DIR, Path)
        assert SRC_DIR.name == "src"

    def test_defines_figures_dir(self):
        from src.config import FIGURES_DIR
        assert isinstance(FIGURES_DIR, Path)

    def test_defines_tables_dir(self):
        from src.config import TABLES_DIR
        assert isinstance(TABLES_DIR, Path)


class TestStubModules:
    """Verify stubs have docstrings and no fake implementations."""

    @pytest.mark.parametrize("module", MODULES)
    def test_module_has_docstring(self, module):
        for key in list(sys.modules.keys()):
            if key.startswith("src"):
                del sys.modules[key]
        mod = importlib.import_module(module)
        assert mod.__doc__ is not None, f"{module} missing docstring"
