"""Plot generation for figures.

Creates publication-quality figures saved to paper/outputs/figures/.
"""
from pathlib import Path


def save_figure(fig, name: str, output_dir: Path | None = None):
    """Save a figure to the outputs directory.

    Args:
        fig: Figure object to save.
        name: Filename (without extension).
        output_dir: Override output directory.
    """
    raise NotImplementedError("Implement during research work phase")
