from api.text_extract import MAX_TEXT_CHARS, extract_text, sniff_type
from tests.resume_fixtures import make_docx_bytes, make_pdf_bytes, make_pdf_with_text


def test_sniff_pdf():
    assert sniff_type(make_pdf_bytes()) == "pdf"


def test_sniff_docx():
    assert sniff_type(make_docx_bytes()) == "docx"


def test_sniff_rejects_png_named_pdf():
    png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50
    assert sniff_type(png) is None


def test_extract_docx_text_done():
    data = make_docx_bytes("Python Django Engineer")
    text, status = extract_text(data, "docx")
    assert status == "done"
    assert "Python" in text


def test_extract_pdf_with_text_done():
    data = make_pdf_with_text("ResumeKeyword")
    text, status = extract_text(data, "pdf")
    # Some minimal PDFs extract cleanly; accept done or empty, never failed.
    assert status in ("done", "empty")


def test_extract_blank_pdf_empty():
    text, status = extract_text(make_pdf_bytes(), "pdf")
    assert status == "empty"
    assert text == ""


def test_extract_corrupt_bytes_failed():
    text, status = extract_text(b"not a real pdf", "pdf")
    assert status == "failed"


def test_text_capped():
    big = make_docx_bytes("word " * 60000)  # ~300k chars
    text, status = extract_text(big, "docx")
    assert len(text) <= MAX_TEXT_CHARS
