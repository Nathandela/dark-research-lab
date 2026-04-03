"""Plot generation for figures.

Creates publication-quality figures saved to paper/outputs/figures/.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

from src.config import FIGURES_DIR


def save_figure(
    fig: plt.Figure,
    name: str,
    output_dir: Path | None = None,
    dpi: int = 300,
) -> Path:
    """Save a matplotlib figure as PDF.

    Args:
        fig: Matplotlib Figure object to save.
        name: Filename without extension.
        output_dir: Override output directory (defaults to FIGURES_DIR).
        dpi: Resolution for raster elements within the PDF.

    Returns:
        Path to the saved file.
    """
    out = output_dir or FIGURES_DIR
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.pdf"
    fig.savefig(path, format="pdf", dpi=dpi, bbox_inches="tight")
    return path
