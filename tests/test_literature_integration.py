"""Integration tests for the literature RAG pipeline.

Tests the full pipeline: drl index processes PDF -> drl knowledge returns results.
These tests require the Go binary to be built at go/dist/drl.
"""
import json
import os
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DRL_BINARY = REPO_ROOT / "go" / "dist" / "drl"


def _skip_if_no_binary():
    if not DRL_BINARY.exists():
        pytest.skip(f"drl binary not found at {DRL_BINARY}")


@pytest.fixture
def test_pdf(tmp_path):
    """Create a test PDF in a temporary literature/pdfs/ structure."""
    import fitz

    pdfs_dir = REPO_ROOT / "literature" / "pdfs"
    pdfs_dir.mkdir(parents=True, exist_ok=True)

    pdf_path = pdfs_dir / "_test_integration.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        textwrap.dedent("""\
            Integration Test Paper on Machine Learning in Finance.
            Abstract: We apply gradient boosting methods to predict stock returns.
            Our model achieves superior out-of-sample performance compared to
            linear regression baselines. The study covers S&P 500 constituents
            from 2010-2023 using quarterly financial data.
        """),
        fontsize=11,
    )
    doc.save(str(pdf_path))
    doc.close()

    yield pdf_path

    # Cleanup
    pdf_path.unlink(missing_ok=True)
    note_path = REPO_ROOT / "literature" / "notes" / "test-integration.md"
    note_path.unlink(missing_ok=True)


class TestDrlIndex:
    def test_index_processes_pdf(self, test_pdf):
        """drl index processes a test PDF and creates searchable entries."""
        _skip_if_no_binary()
        result = subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "chunk(s) created" in result.stdout

    def test_index_generates_summary_note(self, test_pdf):
        """drl index generates a summary note in literature/notes/."""
        _skip_if_no_binary()
        subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        note_path = REPO_ROOT / "literature" / "notes" / "test-integration.md"
        assert note_path.exists(), "Summary note not generated"
        content = note_path.read_text()
        assert "# " in content

    def test_index_idempotent(self, test_pdf):
        """Re-running drl index without changes skips unchanged PDFs."""
        _skip_if_no_binary()
        # First run
        subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Second run without --force
        result = subprocess.run(
            [str(DRL_BINARY), "index"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert "unchanged" in result.stdout


class TestDrlKnowledge:
    def test_knowledge_returns_results(self, test_pdf):
        """drl knowledge returns relevant chunks for a known query."""
        _skip_if_no_binary()
        # Index first
        subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Search
        result = subprocess.run(
            [str(DRL_BINARY), "knowledge", "machine learning finance"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        assert "gradient boosting" in result.stdout or "machine learning" in result.stdout.lower()

    def test_knowledge_json_output(self, test_pdf):
        """drl knowledge --json returns valid JSON with expected fields."""
        _skip_if_no_binary()
        # Index first
        subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        # Search with JSON output
        result = subprocess.run(
            [str(DRL_BINARY), "knowledge", "--json", "stock returns"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        if len(data) > 0:
            item = data[0]
            assert "file" in item
            assert "chunk_text" in item
            assert "similarity" in item


class TestEmbedDaemonHealthCheck:
    def test_embed_flag_without_daemon(self, test_pdf):
        """drl index --embed fails gracefully when daemon is not running."""
        _skip_if_no_binary()
        result = subprocess.run(
            [str(DRL_BINARY), "index", "--embed"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "PATH": ""},  # Ensure daemon not found
        )
        # Should either error or warn about daemon
        assert result.returncode != 0 or "not running" in result.stderr.lower() or "not available" in result.stderr.lower() or "daemon" in result.stderr.lower()
