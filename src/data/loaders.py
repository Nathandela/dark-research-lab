"""Data loading utilities.

Provides functions to load raw datasets from various sources
into Polars DataFrames for analysis.
"""
from pathlib import Path

import polars as pl


def load_csv(
    path: Path,
    schema_overrides: dict[str, pl.DataType] | None = None,
) -> pl.LazyFrame:
    """Load a CSV dataset using Polars lazy scan.

    Uses scan_csv for memory-efficient lazy evaluation. The caller
    should call .collect() when ready to materialize.

    Args:
        path: Path to the CSV file.
        schema_overrides: Optional dict mapping column names to Polars
            dtypes (e.g., {"year": pl.Int32, "gdp": pl.Float64}).

    Returns:
        A Polars LazyFrame ready for chained transformations.

    Example::

        lf = load_csv(
            Path("data/raw/panel.csv"),
            schema_overrides={"year": pl.Int32, "gdp_pc": pl.Float64},
        )
        df = lf.filter(pl.col("year") >= 2000).collect()
    """
    raise NotImplementedError("Implement during research work phase")


def load_dataset(path: Path) -> pl.LazyFrame:
    """Load a dataset from the given path.

    Dispatches to the appropriate loader based on file extension.

    Args:
        path: Path to the data file.

    Returns:
        A Polars LazyFrame.
    """
    raise NotImplementedError("Implement during research work phase")
