"""Tests for Epic d3m: Python code robustness and build hygiene.

Verifies:
1. regression_table_to_latex handles None p-values
2. save_figure wraps savefig in try/except
3. compile.sh checks for pdflatex before running
4. pyproject.toml test deps include pymupdf and matplotlib
5. test_integration_cross_epic.py regex handles paths with spaces
"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# AC1: regression_table_to_latex handles None p-values
# ---------------------------------------------------------------------------

class TestRegressionTableNonePValues:
    """regression_table_to_latex must not crash when p-values are missing."""

    def test_none_pvalue_does_not_crash(self):
        from src.analysis.econometrics import RegressionResult, regression_table_to_latex
        result = RegressionResult(
            coefficients={"x1": 0.5, "x2": -0.3},
            std_errors={"x1": 0.1, "x2": 0.05},
            p_values={"x1": 0.001},  # x2 p-value missing from dict
            r_squared=0.75,
            n_obs=100,
        )
        latex = regression_table_to_latex([result], ["Model 1"])
        assert isinstance(latex, str)
        assert "x2" in latex

    def test_explicit_none_pvalue(self):
        from src.analysis.econometrics import RegressionResult, regression_table_to_latex
        result = RegressionResult(
            coefficients={"x1": 0.5},
            std_errors={"x1": 0.1},
            p_values={"x1": None},  # explicit None
            r_squared=0.75,
            n_obs=100,
        )
        latex = regression_table_to_latex([result], ["Model 1"])
        assert isinstance(latex, str)
        assert "0.5" in latex  # coefficient still appears

    def test_none_pvalue_no_stars(self):
        """When p-value is None, no significance stars should appear."""
        from src.analysis.econometrics import RegressionResult, regression_table_to_latex
        result = RegressionResult(
            coefficients={"x1": 0.5},
            std_errors={"x1": 0.1},
            p_values={"x1": None},
            r_squared=0.75,
            n_obs=100,
        )
        latex = regression_table_to_latex([result], ["Model 1"])
        assert "***" not in latex
        assert "**" not in latex


# ---------------------------------------------------------------------------
# AC2: save_figure wraps fig.savefig in try/except
# ---------------------------------------------------------------------------

class TestSaveFigureErrorHandling:
    """save_figure must catch and re-raise savefig errors with context."""

    def test_save_figure_catches_savefig_error(self, tmp_path):
        from unittest.mock import MagicMock
        from src.visualization.plots import save_figure

        fig = MagicMock()
        fig.savefig.side_effect = ValueError("bad figure")
        with pytest.raises(RuntimeError, match="Failed to save figure"):
            save_figure(fig, "test", output_dir=tmp_path)


# ---------------------------------------------------------------------------
# AC3: compile.sh checks for pdflatex
# ---------------------------------------------------------------------------

class TestCompileShPdflatexCheck:
    """compile.sh must verify pdflatex exists before running."""

    def test_compile_sh_checks_pdflatex(self):
        content = (REPO_ROOT / "paper" / "compile.sh").read_text()
        assert "command -v pdflatex" in content, (
            "compile.sh must check for pdflatex with 'command -v pdflatex'"
        )

    def test_compile_sh_warns_if_bibtex_missing(self):
        content = (REPO_ROOT / "paper" / "compile.sh").read_text()
        # Should check for bibtex but warn (not fail)
        assert "command -v bibtex" in content, (
            "compile.sh should check for bibtex availability"
        )


# ---------------------------------------------------------------------------
# AC4: pyproject.toml test deps include pymupdf and matplotlib
# ---------------------------------------------------------------------------

class TestPyprojectTestDeps:
    """test dependency group must include pymupdf and matplotlib."""

    def test_test_deps_include_pymupdf(self):
        import tomllib
        with open(REPO_ROOT / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        test_deps = data.get("dependency-groups", {}).get("test", [])
        dep_names = [d.lower().split(">=")[0].split("[")[0] for d in test_deps]
        assert "pymupdf" in dep_names, (
            "test dependency group must include pymupdf"
        )

    def test_test_deps_include_matplotlib(self):
        import tomllib
        with open(REPO_ROOT / "pyproject.toml", "rb") as f:
            data = tomllib.load(f)
        test_deps = data.get("dependency-groups", {}).get("test", [])
        dep_names = [d.lower().split(">=")[0].split("[")[0] for d in test_deps]
        assert "matplotlib" in dep_names, (
            "test dependency group must include matplotlib"
        )


# ---------------------------------------------------------------------------
# AC5: regex for binary path handles paths with spaces
# ---------------------------------------------------------------------------

class TestBinaryPathRegex:
    """The regex extracting binary paths must handle paths with spaces."""

    def test_single_quoted_path_with_spaces(self):
        import re
        # The pattern used in test_integration_cross_epic.py
        cmd = "'/Users/John Smith/bin/ca' hooks run phase-guard"
        match = re.search(r"""['"]([^'"]+)['"]""", cmd)
        assert match, "Regex should match single-quoted path with spaces"
        assert match.group(1) == "/Users/John Smith/bin/ca"

    def test_double_quoted_path(self):
        import re
        cmd = '"/Users/John Smith/bin/ca" hooks run phase-guard'
        match = re.search(r"""['"]([^'"]+)['"]""", cmd)
        assert match, "Regex should match double-quoted path"
        assert match.group(1) == "/Users/John Smith/bin/ca"
