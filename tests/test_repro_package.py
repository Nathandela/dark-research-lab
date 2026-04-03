"""Tests for reproducibility package scaffolding (Epic 3)."""
import json
from pathlib import Path

from src.orchestrators.repro import generate_manifest

REPO_ROOT = Path(__file__).parent.parent


class TestReproManifest:
    def test_repro_module_exists(self):
        assert (REPO_ROOT / "src" / "orchestrators" / "repro.py").is_file()

    def test_generate_manifest_callable(self):
        assert callable(generate_manifest)

    def test_manifest_structure(self, tmp_path):
        manifest = generate_manifest(output_dir=tmp_path)
        assert isinstance(manifest, dict)
        assert "python_version" in manifest
        assert "dependencies" in manifest
        assert "data_files" in manifest
        assert "run_command" in manifest
        assert "environment" in manifest

    def test_manifest_writes_to_file(self, tmp_path):
        generate_manifest(output_dir=tmp_path)
        manifest_path = tmp_path / "repro_manifest.json"
        assert manifest_path.is_file()
        data = json.loads(manifest_path.read_text())
        assert "python_version" in data
