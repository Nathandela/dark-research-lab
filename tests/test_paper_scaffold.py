"""Tests for paper/ LaTeX scaffolding (Epic 3)."""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
PAPER_DIR = REPO_ROOT / "paper"
SECTIONS_DIR = PAPER_DIR / "sections"

EXPECTED_SECTIONS = [
    "intro.tex",
    "literature.tex",
    "methodology.tex",
    "data.tex",
    "results.tex",
    "robustness.tex",
    "conclusion.tex",
]

HAS_PDFLATEX = shutil.which("pdflatex") is not None


class TestPaperDirectoryStructure:
    def test_paper_dir_exists(self):
        assert PAPER_DIR.is_dir()

    def test_sections_dir_exists(self):
        assert SECTIONS_DIR.is_dir()

    def test_figures_dir_exists(self):
        assert (PAPER_DIR / "outputs" / "figures").is_dir()

    def test_tables_dir_exists(self):
        assert (PAPER_DIR / "outputs" / "tables").is_dir()

    def test_main_tex_exists(self):
        assert (PAPER_DIR / "main.tex").is_file()

    def test_ref_bib_exists(self):
        assert (PAPER_DIR / "Ref.bib").is_file()

    def test_compile_sh_exists(self):
        assert (PAPER_DIR / "compile.sh").is_file()

    def test_compile_sh_is_executable(self):
        assert os.access(PAPER_DIR / "compile.sh", os.X_OK)

    def test_all_section_stubs_exist(self):
        for section in EXPECTED_SECTIONS:
            assert (SECTIONS_DIR / section).is_file(), f"Missing: {section}"


class TestMainTex:
    @pytest.fixture
    def main_tex(self):
        return (PAPER_DIR / "main.tex").read_text()

    def test_has_documentclass(self, main_tex):
        assert r"\documentclass" in main_tex

    def test_inputs_all_sections(self, main_tex):
        for section in EXPECTED_SECTIONS:
            stem = section.replace(".tex", "")
            assert f"\\input{{sections/{stem}}}" in main_tex, (
                f"Missing \\input for {stem}"
            )

    def test_has_bibliography(self, main_tex):
        assert r"\bibliography{Ref}" in main_tex

    def test_has_title(self, main_tex):
        assert r"\title{" in main_tex

    def test_has_author(self, main_tex):
        assert r"\author{" in main_tex

    def test_has_abstract(self, main_tex):
        assert r"\begin{abstract}" in main_tex


class TestSectionStubs:
    @pytest.mark.parametrize("section", EXPECTED_SECTIONS)
    def test_section_has_section_command(self, section):
        content = (SECTIONS_DIR / section).read_text()
        assert r"\section{" in content or r"\section*{" in content

    @pytest.mark.parametrize("section", EXPECTED_SECTIONS)
    def test_section_has_placeholder(self, section):
        content = (SECTIONS_DIR / section).read_text()
        assert "%" in content or "TODO" in content


class TestCompileScript:
    @pytest.fixture
    def compile_sh(self):
        return (PAPER_DIR / "compile.sh").read_text()

    def test_uses_no_shell_escape(self, compile_sh):
        assert "--no-shell-escape" in compile_sh

    def test_runs_three_passes(self, compile_sh):
        assert compile_sh.count("pdflatex") >= 3

    def test_runs_bibtex(self, compile_sh):
        assert "bibtex" in compile_sh

    @pytest.mark.skipif(not HAS_PDFLATEX, reason="pdflatex not installed")
    def test_compile_produces_pdf(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Copy paper/ contents to temp dir
            shutil.copytree(PAPER_DIR, tmpdir / "paper")
            result = subprocess.run(
                ["bash", "compile.sh"],
                cwd=tmpdir / "paper",
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, f"compile.sh failed:\n{result.stderr}"
            assert (tmpdir / "paper" / "main.pdf").is_file()
