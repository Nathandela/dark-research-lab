"""Tests for the DRL Python wrapper."""
import os
import sys
from pathlib import Path

# Path to the Python wrapper module
WRAPPER_DIR = Path(__file__).parent.parent / "python" / "drl"


def test_wrapper_module_exists():
    """The drl Python package directory exists."""
    assert WRAPPER_DIR.is_dir()


def test_wrapper_has_init():
    """The wrapper package has __init__.py."""
    assert (WRAPPER_DIR / "__init__.py").is_file()


def test_wrapper_has_main():
    """The wrapper package has __main__.py for python -m drl."""
    assert (WRAPPER_DIR / "__main__.py").is_file()


def test_main_function_exists():
    """The main() entry point is importable."""
    # Add parent to path so we can import
    sys.path.insert(0, str(WRAPPER_DIR.parent))
    try:
        from drl import main
        assert callable(main)
    finally:
        sys.path.pop(0)


def test_pyproject_exists():
    """pyproject.toml exists at project root."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    assert pyproject.is_file()


def test_pyproject_has_drl_script():
    """pyproject.toml defines drl entry point."""
    pyproject = Path(__file__).parent.parent / "pyproject.toml"
    content = pyproject.read_text()
    assert "drl" in content
    assert "project.scripts" in content or "[project.scripts]" in content


def test_build_script_exists():
    """Cross-compile build script exists."""
    build_script = Path(__file__).parent.parent / "scripts" / "build.sh"
    assert build_script.is_file()
    assert os.access(build_script, os.X_OK)
