"""Shared test fixtures."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Add repo root at import time so top-level imports in test modules
# (which run during collection, before fixtures) can resolve 'src'.
_root_str = str(REPO_ROOT)
if _root_str not in sys.path:
    sys.path.insert(0, _root_str)
