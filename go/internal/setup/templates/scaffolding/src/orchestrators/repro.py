"""Reproducibility package generator.

Produces a manifest (repro_manifest.json) capturing the environment,
dependencies, data files, and run instructions needed to reproduce
the analysis from scratch.
"""
import hashlib
import json
import platform
from pathlib import Path

from src.config import DATA_DIR, PAPER_DIR, PROJECT_ROOT, SRC_DIR


def _sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def generate_manifest(output_dir: Path | None = None) -> dict:
    """Generate a reproducibility manifest.

    Args:
        output_dir: Directory to write repro_manifest.json.
                    Defaults to paper/ directory.

    Returns:
        Manifest dictionary.
    """
    if output_dir is None:
        output_dir = PAPER_DIR

    analysis_scripts = []
    if SRC_DIR.is_dir():
        for f in sorted(SRC_DIR.rglob("*.py")):
            if f.is_file():
                analysis_scripts.append({
                    "path": str(f.relative_to(PROJECT_ROOT)),
                    "sha256": _sha256(f),
                })

    data_files = []
    if DATA_DIR.is_dir():
        for f in sorted(DATA_DIR.rglob("*")):
            if f.is_file():
                data_files.append({
                    "path": str(f.relative_to(PROJECT_ROOT)),
                    "sha256": _sha256(f),
                })

    uv_lock = PROJECT_ROOT / "uv.lock"
    dependencies = {
        "file": "uv.lock",
        "sha256": _sha256(uv_lock) if uv_lock.is_file() else None,
    }

    environment = {
        "os": platform.system(),
        "arch": platform.machine(),
        "python_version": platform.python_version(),
    }

    reproduction_steps = [
        "git clone <repository-url> && cd <repository>",
        "uv sync  # install exact dependency versions from uv.lock",
        "uv run python -m src.orchestrators.repro  # verify manifest",
        "bash paper/compile.sh  # compile the paper",
    ]

    manifest = {
        "dependencies": dependencies,
        "analysis_scripts": analysis_scripts,
        "data_files": data_files,
        "run_command": "uv run python -m src.orchestrators.repro",
        "environment": environment,
        "reproduction_steps": reproduction_steps,
    }

    output_path = Path(output_dir) / "repro_manifest.json"
    output_path.write_text(json.dumps(manifest, indent=2) + "\n")

    return manifest


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate reproducibility manifest")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()
    generate_manifest(output_dir=args.output_dir)
