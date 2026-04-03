"""Reproducibility package generator.

Produces a manifest (repro_manifest.json) capturing the environment,
dependencies, data files, and run instructions needed to reproduce
the analysis from scratch.
"""
import json
import platform
from pathlib import Path

from src.config import DATA_DIR, PAPER_DIR, PROJECT_ROOT


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

    # Collect data files if data/ exists
    data_files = []
    if DATA_DIR.is_dir():
        data_files = [
            str(f.relative_to(PROJECT_ROOT))
            for f in sorted(DATA_DIR.rglob("*"))
            if f.is_file()
        ]

    manifest = {
        "python_version": platform.python_version(),
        "dependencies": "uv.lock",
        "data_files": data_files,
        "run_command": "uv run python -m src.orchestrators.repro",
        "environment": {
            "os": platform.system(),
            "arch": platform.machine(),
        },
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
