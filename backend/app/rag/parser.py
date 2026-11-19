"""
Ojas Document Parser.

Extracts plain text from requirement documents in DOCX, PDF, and TXT/MD formats.
Uses python-docx, pypdf, and chardet with robust fallbacks.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".docx", ".pdf", ".txt", ".md"}


def detect_file_type(file_path: str | Path) -> str:
    """Infer normalized file type string from file path extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".docx":
        return "docx"
    if ext == ".pdf":
        return "pdf"
    if ext in {".txt", ".md"}:
        return "txt"
    return ext.lstrip(".")


def parse_docx(file_path: str | Path) -> str:
    """
    Extract all paragraph text and table cell contents from a .docx document.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX file not found: {path}")

    try:
        import docx  # python-docx

        doc = docx.Document(str(path))
        lines: list[str] = []

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                lines.append(text)

        # Extract tables
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    lines.append(" | ".join(row_cells))

        return "\n\n".join(lines)

    except Exception as exc:
        logger.exception("Failed to parse DOCX file %s: %s", path, exc)
        raise ValueError(f"Error parsing DOCX file {path.name}: {exc}") from exc


def parse_pdf(file_path: str | Path) -> str:
    """
    Extract text from a .pdf document page by page using pypdf.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    try:
        import pypdf

        reader = pypdf.PdfReader(str(path))
        page_texts: list[str] = []

        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
                cleaned = text.strip()
                if cleaned:
                    page_texts.append(cleaned)
            except Exception as page_exc:
                logger.warning("Could not extract page %d from %s: %s", i + 1, path.name, page_exc)

        return "\n\n".join(page_texts)

    except Exception as exc:
        logger.exception("Failed to parse PDF file %s: %s", path, exc)
        raise ValueError(f"Error parsing PDF file {path.name}: {exc}") from exc


def parse_txt(file_path: str | Path) -> str:
    """
    Read plain text or markdown file with encoding detection via chardet.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Text file not found: {path}")

    try:
        raw_bytes = path.read_bytes()
        if not raw_bytes:
            return ""

        # Detect character encoding
        import chardet

        detected = chardet.detect(raw_bytes)
        encoding = detected.get("encoding") or "utf-8"

        try:
            return raw_bytes.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            # Fallback attempts
            try:
                return raw_bytes.decode("utf-8", errors="replace")
            except Exception:
                return raw_bytes.decode("latin-1", errors="replace")

    except Exception as exc:
        logger.exception("Failed to parse TXT file %s: %s", path, exc)
        raise ValueError(f"Error parsing text file {path.name}: {exc}") from exc


def parse_document(file_path: str | Path, file_type: Optional[str] = None) -> str:
    """
    Extract raw text from a document by routing to the appropriate parser.

    Parameters:
        file_path: Absolute or relative path to the file.
        file_type: Optional type override ("docx", "pdf", "txt", "md").
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Document file does not exist: {path}")

    type_to_use = (file_type or detect_file_type(path)).lower()

    if type_to_use == "docx":
        return parse_docx(path)
    elif type_to_use == "pdf":
        return parse_pdf(path)
    elif type_to_use in {"txt", "md", "markdown"}:
        return parse_txt(path)
    else:
        raise ValueError(
            f"Unsupported file type: '{type_to_use}'. Only docx, pdf, txt, and md are supported."
        )

