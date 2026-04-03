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
def test_repo(tmp_path):
    """Create an isolated repo structure with a test PDF."""
    import fitz

    pdfs_dir = tmp_path / "literature" / "pdfs"
    pdfs_dir.mkdir(parents=True)
    notes_dir = tmp_path / "literature" / "notes"
    notes_dir.mkdir(parents=True)

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

    yield tmp_path


class TestDrlIndex:
    def test_index_processes_pdf(self, test_repo):
        """drl index processes a test PDF and creates searchable entries."""
        _skip_if_no_binary()
        result = subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "DRL_ROOT": str(test_repo)},
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert "chunk(s) created" in result.stdout

    def test_index_generates_summary_note(self, test_repo):
        """drl index generates a summary note in literature/notes/."""
        _skip_if_no_binary()
        subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "DRL_ROOT": str(test_repo)},
        )
        notes = list((test_repo / "literature" / "notes").glob("*.md"))
        assert len(notes) > 0, "Summary note not generated"
        content = notes[0].read_text()
        assert "# " in content

    def test_index_idempotent(self, test_repo):
        """Re-running drl index without changes skips unchanged PDFs."""
        _skip_if_no_binary()
        env = {**os.environ, "DRL_ROOT": str(test_repo)}
        # First run
        subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )
        # Second run without --force
        result = subprocess.run(
            [str(DRL_BINARY), "index"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )
        assert result.returncode == 0
        assert "unchanged" in result.stdout


class TestDrlKnowledge:
    def test_knowledge_returns_results(self, test_repo):
        """drl knowledge returns relevant chunks for a known query."""
        _skip_if_no_binary()
        env = {**os.environ, "DRL_ROOT": str(test_repo)}
        # Index first
        subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )
        # Search
        result = subprocess.run(
            [str(DRL_BINARY), "knowledge", "machine learning finance"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )
        assert result.returncode == 0
        assert "gradient boosting" in result.stdout or "machine learning" in result.stdout.lower()

    def test_knowledge_json_output(self, test_repo):
        """drl knowledge --json returns valid JSON with expected fields."""
        _skip_if_no_binary()
        env = {**os.environ, "DRL_ROOT": str(test_repo)}
        # Index first
        subprocess.run(
            [str(DRL_BINARY), "index", "--force"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
        )
        # Search with JSON output
        result = subprocess.run(
            [str(DRL_BINARY), "knowledge", "--json", "stock returns"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env=env,
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
    def test_embed_flag_without_daemon(self, test_repo):
        """drl index --embed fails gracefully when daemon is not running."""
        _skip_if_no_binary()
        result = subprocess.run(
            [str(DRL_BINARY), "index", "--embed"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            env={**os.environ, "DRL_ROOT": str(test_repo), "PATH": ""},
        )
        # Should either error or warn about daemon
        assert result.returncode != 0 or "not running" in result.stderr.lower() or "not available" in result.stderr.lower() or "daemon" in result.stderr.lower()
