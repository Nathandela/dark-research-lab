"""Tests for reproducibility package scaffolding (Epic 3) and polish (Epic zgo)."""
import json
import subprocess
import textwrap
from pathlib import Path

import pytest

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
        assert "dependencies" in manifest
        assert "data_files" in manifest
        assert "run_command" in manifest
        assert "environment" in manifest
        assert "python_version" in manifest["environment"]

    def test_manifest_writes_to_file(self, tmp_path):
        generate_manifest(output_dir=tmp_path)
        manifest_path = tmp_path / "repro_manifest.json"
        assert manifest_path.is_file()
        data = json.loads(manifest_path.read_text())
        assert "environment" in data


class TestManifestCompleteness:
    """Verify the manifest contains all fields needed for independent replication."""

    def test_manifest_has_script_inventory(self, tmp_path):
        """Manifest must list analysis scripts with SHA-256 checksums."""
        manifest = generate_manifest(output_dir=tmp_path)
        assert "analysis_scripts" in manifest
        scripts = manifest["analysis_scripts"]
        assert isinstance(scripts, list)
        # Each entry should have path and sha256
        for entry in scripts:
            assert "path" in entry
            assert "sha256" in entry
            assert len(entry["sha256"]) == 64  # SHA-256 hex digest length

    def test_manifest_has_data_file_hashes(self, tmp_path, monkeypatch):
        """Data files must include SHA-256 checksums, not just paths."""
        # Create a fake project with data and src directories
        fake_data = tmp_path / "data"
        fake_data.mkdir()
        (fake_data / "sample.csv").write_text("a,b\n1,2\n")
        fake_src = tmp_path / "src"
        fake_src.mkdir()
        (fake_src / "main.py").write_text("print('hello')\n")

        import src.orchestrators.repro as repro_mod

        monkeypatch.setattr(repro_mod, "DATA_DIR", fake_data)
        monkeypatch.setattr(repro_mod, "SRC_DIR", fake_src)
        monkeypatch.setattr(repro_mod, "PROJECT_ROOT", tmp_path)

        out_dir = tmp_path / "output"
        out_dir.mkdir()
        manifest = generate_manifest(output_dir=out_dir)
        data_files = manifest["data_files"]
        assert isinstance(data_files, list)
        assert len(data_files) >= 1
        for entry in data_files:
            assert isinstance(entry, dict)
            assert "path" in entry
            assert "sha256" in entry

    def test_manifest_has_full_environment(self, tmp_path):
        """Environment must include Python version, OS, arch, and uv.lock ref."""
        manifest = generate_manifest(output_dir=tmp_path)
        env = manifest["environment"]
        assert "os" in env
        assert "arch" in env
        assert "python_version" in env

    def test_manifest_has_uv_lock_reference(self, tmp_path):
        """Dependencies must reference uv.lock with its checksum."""
        manifest = generate_manifest(output_dir=tmp_path)
        deps = manifest["dependencies"]
        assert isinstance(deps, dict)
        assert "file" in deps
        assert deps["file"] == "uv.lock"
        assert "sha256" in deps

    def test_manifest_has_reproduction_instructions(self, tmp_path):
        """Manifest must include step-by-step reproduction instructions."""
        manifest = generate_manifest(output_dir=tmp_path)
        assert "reproduction_steps" in manifest
        steps = manifest["reproduction_steps"]
        assert isinstance(steps, list)
        assert len(steps) >= 3  # At minimum: clone, install deps, run

    def test_script_checksums_are_valid_sha256(self, tmp_path):
        """All checksums must be valid 64-char hex strings."""
        manifest = generate_manifest(output_dir=tmp_path)
        for entry in manifest["analysis_scripts"]:
            sha = entry["sha256"]
            assert len(sha) == 64
            assert all(c in "0123456789abcdef" for c in sha)


class TestCompileShErrorPropagation:
    """Verify compile.sh propagates bibtex errors instead of swallowing them."""

    def test_compile_sh_no_silent_bibtex_fallback(self):
        """compile.sh must NOT contain 'bibtex main || true'."""
        compile_sh = REPO_ROOT / "paper" / "compile.sh"
        content = compile_sh.read_text()
        assert "|| true" not in content, (
            "compile.sh still swallows bibtex errors with || true"
        )

    def test_compile_sh_has_bibtex_error_check(self):
        """compile.sh must check bibtex exit code and report errors."""
        compile_sh = REPO_ROOT / "paper" / "compile.sh"
        content = compile_sh.read_text()
        assert "bibtex" in content
        # Must capture and check bibtex exit code
        assert "bibtex_rc" in content or "$?" in content
        # Must have error reporting
        assert "Error" in content or "error" in content


class TestLatexInfrastructure:
    """Verify main.tex has required packages and paths."""

    def test_main_tex_has_required_packages(self):
        """main.tex must include standard academic packages."""
        main_tex = REPO_ROOT / "paper" / "main.tex"
        content = main_tex.read_text()
        required_packages = [
            "siunitx",
            "threeparttable",
            "longtable",
            "caption",
            "subcaption",
            "adjustbox",
            "float",
            "lscape",
        ]
        for pkg in required_packages:
            assert pkg in content, f"main.tex is missing package: {pkg}"

    def test_main_tex_has_tables_graphicspath(self):
        """main.tex must include outputs/tables/ in graphicspath."""
        main_tex = REPO_ROOT / "paper" / "main.tex"
        content = main_tex.read_text()
        assert "outputs/tables/" in content, (
            "main.tex is missing graphicspath for tables"
        )

    def test_ref_bib_has_example_entry(self):
        """Ref.bib must contain at least one example BibTeX entry."""
        ref_bib = REPO_ROOT / "paper" / "Ref.bib"
        content = ref_bib.read_text()
        assert "@" in content, "Ref.bib has no BibTeX entries"
        # Should have standard required fields
        assert "author" in content.lower()
        assert "title" in content.lower()
        assert "year" in content.lower()

    def test_section_stubs_have_structural_hints(self):
        """Section stubs must include subsection structure, not just TODOs."""
        sections_dir = REPO_ROOT / "paper" / "sections"
        for tex_file in sorted(sections_dir.glob("*.tex")):
            content = tex_file.read_text()
            assert "\\subsection" in content, (
                f"{tex_file.name} lacks structural hints (no \\subsection found)"
            )
