"""Shared test fixtures for the DRL research project."""
from pathlib import Path

import pytest

from src.config import PROJECT_ROOT


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture
def sample_data_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test data files."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir
