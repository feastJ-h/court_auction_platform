from dataclasses import dataclass
from pathlib import Path

from backend.config import get_settings, processed_dir
from backend.parser.shredder import mask_pii


MIN_TEXT_LENGTH = 100


@dataclass(frozen=True)
class ParsedFile:
    source_path: Path
    processed_path: Path
    extracted_text: str
    parse_status: str
    mask_count: int


class UnsupportedDocumentError(ValueError):
    pass


def extract_raw_text(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        import pdfplumber

        text_parts: list[str] = []
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts).strip()

    if suffix in {".hwp", ".hwpx"}:
        try:
            from hwp5.hwp5txt import extract_text as hwp_extract_text
        except Exception as exc:
            raise UnsupportedDocumentError("HWP parser is not available in this runtime") from exc
        return hwp_extract_text(str(path)).strip()

    raise UnsupportedDocumentError(f"Unsupported document type: {suffix}")


def extract_document(file_path: str | Path) -> ParsedFile:
    settings = get_settings()
    source_path = Path(file_path)
    raw_text = extract_raw_text(source_path)
    mask_count = 0
    final_text = raw_text

    if settings.enable_pii_masking:
        final_text, mask_count = mask_pii(raw_text)

    if len(final_text) >= MIN_TEXT_LENGTH:
        parse_status = "PARSED"
    elif source_path.suffix.lower() == ".pdf" and not final_text:
        parse_status = "OCR_REQUIRED"
    else:
        parse_status = "MANUAL_REVIEW"
    target_path = processed_dir() / f"{source_path.stem}.txt"
    target_path.write_text(final_text, encoding="utf-8")

    return ParsedFile(
        source_path=source_path,
        processed_path=target_path,
        extracted_text=final_text,
        parse_status=parse_status,
        mask_count=mask_count,
    )
