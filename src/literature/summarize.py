"""Generate paper summary notes from extracted PDF text."""
from pathlib import Path

from src.literature.extract import make_slug

# Maximum characters of extracted text to include in the summary excerpt.
MAX_EXCERPT_CHARS = 500


def generate_summary(text: str, metadata: dict, notes_dir: Path | str) -> Path:
    """Generate a summary markdown file for a paper.

    Args:
        text: Extracted text from the PDF.
        metadata: Dict from extract_metadata (title, author, page_count, filename).
        notes_dir: Directory to write the summary file.

    Returns:
        Path to the generated summary file.
    """
    notes_dir = Path(notes_dir)
    notes_dir.mkdir(parents=True, exist_ok=True)

    slug = make_slug(metadata["filename"])
    out_path = notes_dir / f"{slug}.md"

    title = metadata.get("title", slug)
    author = metadata.get("author", "")
    page_count = metadata.get("page_count", 0)

    excerpt = text.strip()[:MAX_EXCERPT_CHARS]
    if len(text.strip()) > MAX_EXCERPT_CHARS:
        excerpt += "..."

    lines = [
        f"# {title}",
        "",
        f"- **Source:** `{metadata.get('filename', '')}`",
    ]
    if author:
        lines.append(f"- **Author:** {author}")
    lines.append(f"- **Pages:** {page_count}")
    lines.extend([
        "",
        "## Excerpt",
        "",
        excerpt,
        "",
    ])

    out_path.write_text("\n".join(lines))
    return out_path
