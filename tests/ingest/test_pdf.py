"""Tests for paperlab.ingest.pdf — no real docling import."""
from pathlib import Path

import pytest
from pydantic import ValidationError

from paperlab.ingest import IngestError, IngestedPaper, extract_text


# ---------------------------------------------------------------------------
# Fake converter helpers — no docling dependency
# ---------------------------------------------------------------------------

class _FakeDocument:
    def __init__(self, text: str, title=None):
        self._text = text
        if title is not None:
            self.title = title

    def export_to_markdown(self) -> str:
        return self._text


class _FakeResult:
    def __init__(self, text: str, pages=None, title=None):
        self.document = _FakeDocument(text, title=title)
        if pages is not None:
            self.pages = pages


class _FakeConverter:
    def __init__(self, text: str = "Fake paper text", pages=None, title=None):
        self._text = text
        self._pages = pages
        self._title = title

    def convert(self, path: str) -> _FakeResult:
        return _FakeResult(self._text, pages=self._pages, title=self._title)


class _FailConverter:
    def convert(self, path: str):
        raise RuntimeError("boom")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_file_not_found(tmp_path):
    missing = tmp_path / "ghost.pdf"
    with pytest.raises(FileNotFoundError):
        extract_text(missing)


def test_non_pdf_extension(tmp_path):
    txt_file = tmp_path / "paper.txt"
    txt_file.write_bytes(b"")
    with pytest.raises(ValueError):
        extract_text(txt_file)


def test_non_pdf_uppercase(tmp_path):
    f = tmp_path / "paper.TXT"
    f.write_bytes(b"")
    with pytest.raises(ValueError):
        extract_text(f)


def test_success_basic(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"")

    converter = _FakeConverter(text="Fake paper text", pages=[1, 2, 3])
    result = extract_text(pdf, converter=converter)

    assert isinstance(result, IngestedPaper)
    assert result.text == "Fake paper text"
    assert result.num_pages == 3
    assert result.backend == "docling"
    assert result.source_path == str(pdf)
    assert result.title is None


def test_title_present(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"")

    converter = _FakeConverter(text="Some text", pages=[1], title="T")
    result = extract_text(pdf, converter=converter)

    assert result.title == "T"


def test_title_absent(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"")

    converter = _FakeConverter(text="Some text", pages=[1])
    result = extract_text(pdf, converter=converter)

    assert result.title is None


def test_pages_attribute_missing(tmp_path):
    """Result without .pages attribute → num_pages is None."""
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"")

    # pages=None means _FakeResult won't set .pages
    converter = _FakeConverter(text="text", pages=None)
    result = extract_text(pdf, converter=converter)

    assert result.num_pages is None


def test_ingest_error_wraps_exception(tmp_path):
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"")

    with pytest.raises(IngestError) as exc_info:
        extract_text(pdf, converter=_FailConverter())

    exc = exc_info.value
    assert "boom" in str(exc)
    assert str(pdf) in str(exc)
    assert isinstance(exc.__cause__, RuntimeError)


def test_ingest_error_is_exception():
    assert issubclass(IngestError, Exception)


def test_pydantic_valid():
    paper = IngestedPaper(source_path="x", text="y", backend="docling")
    assert paper.source_path == "x"
    assert paper.text == "y"
    assert paper.title is None
    assert paper.num_pages is None


def test_pydantic_missing_text():
    with pytest.raises(ValidationError):
        IngestedPaper(source_path="x", backend="docling")  # type: ignore[call-arg]
