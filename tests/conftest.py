"""Shared test fixtures."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent


@pytest.fixture(autouse=True)
def _src_on_path():
    """Ensure repo root is on sys.path for src imports."""
    root_str = str(REPO_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    yield
    if root_str in sys.path:
        sys.path.remove(root_str)
