"""Econometric analysis.

Implements the main empirical models (e.g., OLS, IV, panel methods)
for the paper's Results section.
"""
from __future__ import annotations

from dataclasses import dataclass

import polars as pl


@dataclass
class RegressionResult:
    """Container for regression estimation results.

    Attributes:
        coefficients: Map of variable name to estimated coefficient.
        std_errors: Map of variable name to standard error.
        p_values: Map of variable name to p-value.
        r_squared: R-squared of the model.
        n_obs: Number of observations used.
    """
    coefficients: dict[str, float]
    std_errors: dict[str, float]
    p_values: dict[str, float]
    r_squared: float
    n_obs: int


def estimate_main_model(data: pl.DataFrame) -> RegressionResult:
    """Run the primary econometric specification.

    Args:
        data: Analysis-ready dataset.

    Returns:
        RegressionResult with estimated coefficients, standard errors,
        p-values, R-squared, and observation count.
    """
    raise NotImplementedError("Implement during research work phase")


def regression_table_to_latex(
    results: list[RegressionResult],
    model_names: list[str],
    caption: str = "Regression Results",
    label: str = "tab:regression",
) -> str:
    """Format regression results as a LaTeX tabular string.

    Produces a publication-style regression table with coefficients,
    standard errors in parentheses, and significance stars.

    Args:
        results: List of RegressionResult objects (one per column).
        model_names: Display names for each model column.
        caption: Table caption.
        label: LaTeX label for cross-referencing.

    Returns:
        LaTeX string with a tabular environment.
    """
    all_vars = []
    for r in results:
        for v in r.coefficients:
            if v not in all_vars:
                all_vars.append(v)

    ncols = len(results)
    col_spec = "l" + "c" * ncols
    lines = [
        f"\\begin{{table}}[htbp]",
        f"\\centering",
        f"\\caption{{{caption}}}",
        f"\\label{{{label}}}",
        f"\\begin{{tabular}}{{{col_spec}}}",
        "\\hline\\hline",
        " & ".join([""] + model_names) + " \\\\",
        "\\hline",
    ]

    for var in all_vars:
        coef_cells = []
        se_cells = []
        for r in results:
            c = r.coefficients.get(var)
            se = r.std_errors.get(var)
            p = r.p_values.get(var)
            if c is not None:
                stars = "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else ""
                coef_cells.append(f"{c:.4f}{stars}")
                se_cells.append(f"({se:.4f})")
            else:
                coef_cells.append("")
                se_cells.append("")
        lines.append(" & ".join([var] + coef_cells) + " \\\\")
        lines.append(" & ".join([""] + se_cells) + " \\\\")

    lines.append("\\hline")
    obs_cells = [str(r.n_obs) for r in results]
    r2_cells = [f"{r.r_squared:.4f}" for r in results]
    lines.append(" & ".join(["N"] + obs_cells) + " \\\\")
    lines.append(" & ".join(["$R^2$"] + r2_cells) + " \\\\")
    lines.append("\\hline\\hline")
    lines.append("\\end{tabular}")
    lines.append("\\end{table}")

    return "\n".join(lines)
