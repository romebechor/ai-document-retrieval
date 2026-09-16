"""
Text extraction utilities.

Supports extracting clean, plain text from PDF and DOCX files.
Raises well-defined exceptions so callers can handle each error case
distinctly (missing file, unsupported type, no extractable text).
"""

import os
import re


class ExtractionError(Exception):
    """Base class for all text-extraction related errors."""


class FileNotFoundExtractionError(ExtractionError):
    pass


class UnsupportedFileTypeError(ExtractionError):
    pass


class NoTextExtractedError(ExtractionError):
    pass


SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def _clean_text(raw_text: str) -> str:
    """Normalize whitespace while preserving paragraph breaks."""
    # Collapse repeated spaces/tabs, but keep newlines for paragraph splitting.
    text = re.sub(r"[ \t]+", " ", raw_text)
    # Collapse 3+ newlines into a double newline (paragraph separator).
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pdf(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    pages_text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        pages_text.append(page_text)
    return "\n\n".join(pages_text)


def _extract_docx(file_path: str) -> str:
    import docx

    document = docx.Document(file_path)
    paragraphs = [p.text for p in document.paragraphs]
    return "\n\n".join(paragraphs)


def extract_text(file_path: str) -> str:
    """
    Extract clean text from a PDF or DOCX file.

    Raises:
        FileNotFoundExtractionError: the file does not exist.
        UnsupportedFileTypeError: the file extension is not .pdf/.docx.
        NoTextExtractedError: the file was read but no text could be extracted
            (e.g. a scanned PDF with no OCR layer, or an empty document).
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundExtractionError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext}'. Supported types: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    if ext == ".pdf":
        raw_text = _extract_pdf(file_path)
    else:
        raw_text = _extract_docx(file_path)

    cleaned = _clean_text(raw_text)

    if not cleaned:
        raise NoTextExtractedError(
            f"No extractable text found in '{file_path}'. "
            f"The file may be empty, image-only, or scanned without OCR."
        )

    return cleaned
