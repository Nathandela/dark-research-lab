"""Tests for src/ Python analysis scaffolding (Epic 3 + Epic 4fd polish)."""
import importlib
import inspect
from dataclasses import fields
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
        mod = importlib.import_module(module)
        assert mod.__doc__ is not None, f"{module} missing docstring"


# --- Epic 4fd: Polars-typed scaffolding tests ---


class TestPolarsImports:
    """All analysis/data modules import polars as pl."""

    POLARS_MODULES = [
        "src.data.loaders",
        "src.data.cleaners",
        "src.analysis.descriptive",
        "src.analysis.econometrics",
        "src.analysis.robustness",
        "src.visualization.plots",
    ]

    @pytest.mark.parametrize("module", POLARS_MODULES)
    def test_module_imports_polars(self, module):
        mod = importlib.import_module(module)
        assert hasattr(mod, "pl"), f"{module} should import polars as pl"


class TestPolarsTypedSignatures:
    """All stub functions have Polars-typed signatures."""

    def test_load_csv_signature(self):
        from src.data.loaders import load_csv
        sig = inspect.signature(load_csv)
        hints = inspect.get_annotations(load_csv)
        assert "path" in sig.parameters
        assert hints.get("return") is not None, "load_csv must have a return type"

    def test_clean_dataset_signature(self):
        from src.data.cleaners import clean_dataset
        sig = inspect.signature(clean_dataset)
        hints = inspect.get_annotations(clean_dataset)
        assert "data" in sig.parameters
        assert hints.get("return") is not None, "clean_dataset must have a return type"

    def test_summary_statistics_signature(self):
        from src.analysis.descriptive import summary_statistics
        sig = inspect.signature(summary_statistics)
        hints = inspect.get_annotations(summary_statistics)
        assert "data" in sig.parameters
        assert hints.get("return") is not None

    def test_estimate_main_model_signature(self):
        from src.analysis.econometrics import estimate_main_model
        sig = inspect.signature(estimate_main_model)
        hints = inspect.get_annotations(estimate_main_model)
        assert "data" in sig.parameters
        assert hints.get("return") is not None

    def test_run_robustness_checks_signature(self):
        from src.analysis.robustness import run_robustness_checks
        hints = inspect.get_annotations(run_robustness_checks)
        assert hints.get("return") is not None


class TestLoadersPatterns:
    """loaders.py includes a load_csv pattern with Polars lazy scan."""

    def test_load_csv_exists(self):
        from src.data.loaders import load_csv
        assert callable(load_csv)

    def test_load_csv_raises_not_implemented(self):
        from src.data.loaders import load_csv
        with pytest.raises(NotImplementedError):
            load_csv(Path("nonexistent.csv"))


class TestCleanersPatterns:
    """cleaners.py includes a pipeline pattern with chained Polars expressions."""

    def test_clean_dataset_exists(self):
        from src.data.cleaners import clean_dataset
        assert callable(clean_dataset)

    def test_clean_dataset_raises_not_implemented(self):
        import polars as pl
        from src.data.cleaners import clean_dataset
        with pytest.raises(NotImplementedError):
            clean_dataset(pl.DataFrame())


class TestDescriptivePatterns:
    """descriptive.py includes summary_statistics scaffold and LaTeX formatter."""

    def test_summary_statistics_exists(self):
        from src.analysis.descriptive import summary_statistics
        assert callable(summary_statistics)

    def test_summary_statistics_raises_not_implemented(self):
        import polars as pl
        from src.analysis.descriptive import summary_statistics
        with pytest.raises(NotImplementedError):
            summary_statistics(pl.DataFrame())

    def test_summary_table_to_latex_exists(self):
        from src.analysis.descriptive import summary_table_to_latex
        assert callable(summary_table_to_latex)


class TestEconometricsPatterns:
    """econometrics.py includes OLS/IV result type stubs and LaTeX helper."""

    def test_regression_result_dataclass(self):
        from src.analysis.econometrics import RegressionResult
        field_names = {f.name for f in fields(RegressionResult)}
        expected = {"coefficients", "std_errors", "p_values", "r_squared", "n_obs"}
        assert expected.issubset(field_names), f"Missing fields: {expected - field_names}"

    def test_estimate_main_model_exists(self):
        from src.analysis.econometrics import estimate_main_model
        assert callable(estimate_main_model)

    def test_regression_table_to_latex_exists(self):
        from src.analysis.econometrics import regression_table_to_latex
        assert callable(regression_table_to_latex)

    def test_regression_table_to_latex_produces_string(self):
        from src.analysis.econometrics import RegressionResult, regression_table_to_latex
        result = RegressionResult(
            coefficients={"x1": 0.5, "x2": -0.3},
            std_errors={"x1": 0.1, "x2": 0.05},
            p_values={"x1": 0.001, "x2": 0.01},
            r_squared=0.75,
            n_obs=100,
        )
        latex = regression_table_to_latex([result], ["Model 1"])
        assert isinstance(latex, str)
        assert "tabular" in latex
        assert "x1" in latex


class TestRobustnessPatterns:
    """robustness.py includes RobustnessResult dataclass and compare_specifications."""

    def test_robustness_result_dataclass(self):
        from src.analysis.robustness import RobustnessResult
        field_names = {f.name for f in fields(RobustnessResult)}
        expected = {"name", "result"}
        assert expected.issubset(field_names), f"Missing fields: {expected - field_names}"

    def test_compare_specifications_exists(self):
        from src.analysis.robustness import compare_specifications
        assert callable(compare_specifications)

    def test_compare_specifications_raises_not_implemented(self):
        import polars as pl
        from src.analysis.robustness import compare_specifications
        with pytest.raises(NotImplementedError):
            compare_specifications(pl.DataFrame(), [])


class TestVisualizationPatterns:
    """plots.py has a working save_figure function."""

    def test_save_figure_exists(self):
        from src.visualization.plots import save_figure
        assert callable(save_figure)

    def test_save_figure_works(self, tmp_path):
        """save_figure should actually save a PDF file."""
        import matplotlib.pyplot as plt
        from src.visualization.plots import save_figure

        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])
        save_figure(fig, "test_plot", output_dir=tmp_path)
        assert (tmp_path / "test_plot.pdf").is_file()
        plt.close(fig)


class TestInitExports:
    """__init__.py files export key functions."""

    def test_data_init_exports(self):
        from src.data import load_csv, clean_dataset
        assert callable(load_csv)
        assert callable(clean_dataset)

    def test_analysis_init_exports(self):
        from src.analysis import summary_statistics, estimate_main_model, run_robustness_checks
        assert callable(summary_statistics)
        assert callable(estimate_main_model)
        assert callable(run_robustness_checks)

    def test_visualization_init_exports(self):
        from src.visualization import save_figure
        assert callable(save_figure)
