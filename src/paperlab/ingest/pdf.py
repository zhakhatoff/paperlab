"""PDF text extraction for paperlab."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel


class IngestError(Exception):
    """Raised when PDF conversion fails."""


class IngestedPaper(BaseModel):
    source_path: str
    title: str | None = None
    text: str
    num_pages: int | None = None
    backend: str


def extract_text(path: Path | str, converter=None) -> IngestedPaper:
    """Extract text from a PDF file.

    Parameters
    ----------
    path:
        Path to the PDF file.
    converter:
        Optional docling DocumentConverter instance. Created lazily if None.

    Returns
    -------
    IngestedPaper
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix!r} ({path})")

    if converter is None:
        from docling.document_converter import DocumentConverter  # lazy import

        converter = DocumentConverter()

    try:
        result = converter.convert(str(path))
    except Exception as exc:
        raise IngestError(f"Failed to convert {path}: {exc}") from exc

    text = result.document.export_to_markdown()

    num_pages: int | None = None
    if hasattr(result, "pages"):
        num_pages = len(result.pages)

    title: str | None = None
    if hasattr(result.document, "title"):
        title = result.document.title

    return IngestedPaper(
        source_path=str(path),
        title=title,
        text=text,
        num_pages=num_pages,
        backend="docling",
    )
