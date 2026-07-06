from pathlib import Path

from backend.parser.extractor import extract_document
from backend.parser.shredder import mask_pii


def test_shredder_function() -> None:
    masked, count = mask_pii("채무자 900101-1234567 연락처 010-1234-5678 사무실 02-6205-8545")
    assert "900101-1234567" not in masked
    assert "010-1234-5678" not in masked
    assert "02-6205-8545" not in masked
    assert count == 3


def test_extract_downloaded_pdf_if_available() -> None:
    pdfs = sorted(Path("storage/raw_quarantine").glob("*.pdf"))
    if not pdfs:
        print("No downloaded PDF found; parser integration skipped")
        return
    parsed = extract_document(pdfs[0])
    assert parsed.processed_path.exists()
    assert parsed.parse_status in {"PARSED", "MANUAL_REVIEW", "OCR_REQUIRED"}
    assert parsed.extracted_text


if __name__ == "__main__":
    test_shredder_function()
    test_extract_downloaded_pdf_if_available()
    print("Sprint 5 parser tests passed")
