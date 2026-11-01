"""Sniff resume file types and extract plain text.

Extraction never raises to the view: any failure returns ``text_status == "failed"``.
"""

import logging
import zipfile
from io import BytesIO

logger = logging.getLogger("api")

MAX_TEXT_CHARS = 200_000
_MAX_PDF_PAGES = 50
_MAX_DOCX_UNCOMPRESSED = 50 * 1024 * 1024  # zip-bomb guard


def sniff_type(data: bytes) -> str | None:
    """Return ``"pdf"``, ``"docx"`` or ``None`` based on content, not filename."""
    if data[:5] == b"%PDF-":
        return "pdf"
    if zipfile.is_zipfile(BytesIO(data)):
        try:
            with zipfile.ZipFile(BytesIO(data)) as zf:
                names = zf.namelist()
                if "word/document.xml" not in names:
                    return None
                total = sum(info.file_size for info in zf.infolist())
                if total > _MAX_DOCX_UNCOMPRESSED:
                    return None
                return "docx"
        except zipfile.BadZipFile:
            return None
    return None


def _normalise(text: str) -> str:
    text = " ".join(text.split())
    return text[:MAX_TEXT_CHARS]


def _extract_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF")
    parts = []
    for page in reader.pages[:_MAX_PDF_PAGES]:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def _extract_docx(data: bytes) -> str:
    import docx

    document = docx.Document(BytesIO(data))
    parts = [p.text for p in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def extract_text(data: bytes, file_type: str) -> tuple[str, str]:
    """Return ``(text, status)`` where status is ``done``, ``empty`` or ``failed``."""
    try:
        if file_type == "pdf":
            raw = _extract_pdf(data)
        elif file_type == "docx":
            raw = _extract_docx(data)
        else:
            return "", "failed"
    except Exception:
        logger.exception("Resume text extraction failed")
        return "", "failed"

    text = _normalise(raw)
    if not text:
        return "", "empty"
    return text, "done"
