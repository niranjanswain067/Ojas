"""
Unit tests for Document Parser (Phase 13).
"""

from pathlib import Path
import docx
import pypdf
import pytest

from backend.app.rag.parser import (
    detect_file_type,
    parse_document,
    parse_docx,
    parse_pdf,
    parse_txt,
)


@pytest.fixture
def temp_docs_dir(tmp_path: Path):
    """Fixture providing a temporary directory for document creation."""
    doc_dir = tmp_path / "docs"
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir


def test_detect_file_type():
    """Verify extension mapping."""
    assert detect_file_type("requirements.docx") == "docx"
    assert detect_file_type("SRS.pdf") == "pdf"
    assert detect_file_type("spec.txt") == "txt"
    assert detect_file_type("README.md") == "txt"
    assert detect_file_type("archive.zip") == "zip"


def test_parse_txt(temp_docs_dir: Path):
    """Verify parsing plain text files."""
    txt_file = temp_docs_dir / "sample.txt"
    content = "System Requirements:\nREQ-001: The system shall support user authentication."
    txt_file.write_text(content, encoding="utf-8")

    result = parse_txt(txt_file)
    assert "REQ-001" in result
    assert "user authentication" in result

    # Test via parse_document
    routed_result = parse_document(txt_file)
    assert routed_result == result


def test_parse_docx(temp_docs_dir: Path):
    """Verify parsing docx documents with paragraphs and tables."""
    docx_file = temp_docs_dir / "spec.docx"

    doc = docx.Document()
    doc.add_heading("Library Management System", level=1)
    doc.add_paragraph("REQ-002: Add new book to library catalog.")

    table = doc.add_table(rows=2, cols=2)
    table.rows[0].cells[0].text = "Field"
    table.rows[0].cells[1].text = "Description"
    table.rows[1].cells[0].text = "ISBN"
    table.rows[1].cells[1].text = "Unique book identifier"

    doc.save(str(docx_file))

    result = parse_docx(docx_file)
    assert "Library Management System" in result
    assert "REQ-002" in result
    assert "ISBN | Unique book identifier" in result or ("ISBN" in result and "Unique book identifier" in result)


def test_parse_pdf(temp_docs_dir: Path):
    """Verify parsing PDF files."""
    pdf_file = temp_docs_dir / "requirements.pdf"

    # Create a minimal valid PDF using pypdf
    writer = pypdf.PdfWriter()
    page = writer.add_blank_page(width=300, height=300)

    # Note: blank page returns empty or minimal text
    with open(pdf_file, "wb") as f:
        writer.write(f)

    # Should not raise exception even for blank pdf
    result = parse_pdf(pdf_file)
    assert isinstance(result, str)


def test_unsupported_file_type_raises(temp_docs_dir: Path):
    """Unsupported extension should raise ValueError."""
    bad_file = temp_docs_dir / "danger.exe"
    bad_file.write_bytes(b"\x00\x01\x02")

    with pytest.raises(ValueError, match="Unsupported file type"):
        parse_document(bad_file)


def test_nonexistent_file_raises(temp_docs_dir: Path):
    """Nonexistent path should raise FileNotFoundError."""
    missing = temp_docs_dir / "missing.txt"
    with pytest.raises(FileNotFoundError):
        parse_document(missing)

