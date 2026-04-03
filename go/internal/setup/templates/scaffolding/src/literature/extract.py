"""PDF text extraction for the literature RAG pipeline.

Uses PyMuPDF (fitz) for fast, accurate text extraction from academic papers.
"""
import json
import sys
from pathlib import Path

import fitz


def extract_text(pdf_path: Path | str) -> str:
    """Extract all text from a PDF file, page by page.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Concatenated text from all pages.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not a valid PDF.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise ValueError(f"{pdf_path.name} is not a valid PDF: {exc}") from exc

    try:
        pages = []
        for page in doc:
            pages.append(page.get_text())
        return "\n".join(pages)
    finally:
        doc.close()


def extract_metadata(pdf_path: Path | str) -> dict:
    """Extract metadata from a PDF file.

    Returns:
        Dict with keys: title, author, page_count, creation_date, filename.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as exc:
        raise ValueError(f"{pdf_path.name} is not a valid PDF: {exc}") from exc

    try:
        meta = doc.metadata or {}
        page_count = len(doc)
    finally:
        doc.close()

    title = (meta.get("title") or "").strip()
    if not title:
        title = pdf_path.stem

    return {
        "title": title,
        "author": (meta.get("author") or "").strip(),
        "page_count": page_count,
        "creation_date": (meta.get("creationDate") or "").strip(),
        "filename": pdf_path.name,
    }
