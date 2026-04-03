"""PDF text extraction for the literature RAG pipeline.

Uses PyMuPDF (fitz) for fast, accurate text extraction from academic papers.
Can be called as a module: python -m src.literature.extract [--json] <pdf_path>
"""
import json
import re
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


def make_slug(filename: str) -> str:
    """Convert a filename to a URL-safe slug.

    Strips the extension, lowercases, replaces non-alphanumeric with dashes,
    and collapses consecutive dashes.
    """
    stem = Path(filename).stem
    slug = stem.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def _cli_main() -> int:
    """CLI entry point for subprocess extraction."""
    args = sys.argv[1:]
    json_mode = "--json" in args
    if json_mode:
        args.remove("--json")

    if not args:
        print("Usage: python -m src.literature.extract [--json] <pdf_path>", file=sys.stderr)
        return 1

    # Redirect PyMuPDF C-library warnings away from stdout to prevent JSON corruption
    _real_stdout = sys.stdout
    sys.stdout = sys.stderr

    pdf_path = Path(args[0])
    try:
        text = extract_text(pdf_path)
        if json_mode:
            meta = extract_metadata(pdf_path)
            sys.stdout = _real_stdout
            print(json.dumps({"text": text, "metadata": meta}))
        else:
            sys.stdout = _real_stdout
            print(text)
    except (FileNotFoundError, ValueError) as exc:
        sys.stdout = _real_stdout
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli_main())
