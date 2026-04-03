"""Tests for the literature RAG pipeline: PDF extraction, summarization, and indexing."""
import json
import subprocess
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest


def _pymupdf_arch_mismatch() -> bool:
    """Check if pymupdf native library architecture mismatches the Python interpreter."""
    try:
        import fitz
        # If import succeeds, no mismatch
        return False
    except ImportError:
        return True


_skip_arch_mismatch = pytest.mark.skipif(
    _pymupdf_arch_mismatch(),
    reason="pymupdf native library architecture mismatches Python interpreter",
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_pdf(tmp_path):
    """Create a minimal valid PDF for testing."""
    import fitz  # PyMuPDF

    pdf_path = tmp_path / "test_paper.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Title: Test Research Paper", fontsize=16)
    page.insert_text(
        (72, 120),
        textwrap.dedent("""\
            Abstract: This paper investigates the effects of X on Y.
            We find significant results using OLS regression.

            1. Introduction
            Research on X has been growing. This paper contributes
            by examining the relationship between X and Y using
            a novel dataset from 2020-2025.

            2. Methodology
            We employ ordinary least squares regression with
            robust standard errors clustered at the firm level.

            3. Results
            Our findings suggest a positive and significant
            relationship between X and Y (beta=0.42, p<0.01).
        """),
        fontsize=11,
    )
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def multi_page_pdf(tmp_path):
    """Create a multi-page PDF for testing."""
    import fitz

    pdf_path = tmp_path / "multi_page.pdf"
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page()
        page.insert_text((72, 72), f"Page {i + 1} content about economics and finance.")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def empty_pdf(tmp_path):
    """Create an empty PDF (no text)."""
    import fitz

    pdf_path = tmp_path / "empty.pdf"
    doc = fitz.open()
    doc.new_page()
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture
def literature_dir(tmp_path):
    """Create a literature directory structure."""
    pdfs_dir = tmp_path / "literature" / "pdfs"
    notes_dir = tmp_path / "literature" / "notes"
    pdfs_dir.mkdir(parents=True)
    notes_dir.mkdir(parents=True)
    return tmp_path / "literature"


# ---------------------------------------------------------------------------
# extract.py tests
# ---------------------------------------------------------------------------


class TestExtractText:
    def test_extracts_text_from_pdf(self, sample_pdf):
        from src.literature.extract import extract_text

        text = extract_text(sample_pdf)
        assert "Test Research Paper" in text
        assert "OLS regression" in text

    def test_extracts_all_pages(self, multi_page_pdf):
        from src.literature.extract import extract_text

        text = extract_text(multi_page_pdf)
        assert "Page 1" in text
        assert "Page 2" in text
        assert "Page 3" in text

    def test_returns_empty_for_empty_pdf(self, empty_pdf):
        from src.literature.extract import extract_text

        text = extract_text(empty_pdf)
        assert text.strip() == ""

    def test_raises_on_missing_file(self, tmp_path):
        from src.literature.extract import extract_text

        with pytest.raises(FileNotFoundError):
            extract_text(tmp_path / "nonexistent.pdf")

    def test_raises_on_invalid_file(self, tmp_path):
        from src.literature.extract import extract_text

        bad_file = tmp_path / "not_a_pdf.pdf"
        bad_file.write_text("this is not a pdf")
        with pytest.raises(ValueError, match="not a valid PDF"):
            extract_text(bad_file)


class TestExtractMetadata:
    def test_extracts_page_count(self, multi_page_pdf):
        from src.literature.extract import extract_metadata

        meta = extract_metadata(multi_page_pdf)
        assert meta["page_count"] == 3

    def test_returns_filename_as_fallback_title(self, sample_pdf):
        from src.literature.extract import extract_metadata

        meta = extract_metadata(sample_pdf)
        # If PDF has no title metadata, filename stem is used
        assert "title" in meta
        assert isinstance(meta["title"], str)
        assert len(meta["title"]) > 0


# ---------------------------------------------------------------------------
# CLI extraction script tests
# ---------------------------------------------------------------------------


class TestCLIExtract:
    @_skip_arch_mismatch
    def test_cli_extract_outputs_text(self, sample_pdf):
        """The extraction script can be called as a subprocess."""
        result = subprocess.run(
            ["python3", "-m", "src.literature.extract", str(sample_pdf)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert "Test Research Paper" in result.stdout

    @_skip_arch_mismatch
    def test_cli_extract_json_mode(self, sample_pdf):
        """The extraction script outputs JSON with --json flag."""
        result = subprocess.run(
            ["python3", "-m", "src.literature.extract", "--json", str(sample_pdf)],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "text" in data
        assert "metadata" in data
        assert "Test Research Paper" in data["text"]

    def test_cli_extract_missing_file(self, tmp_path):
        """The extraction script returns non-zero for missing files."""
        result = subprocess.run(
            ["python3", "-m", "src.literature.extract", str(tmp_path / "nope.pdf")],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0
