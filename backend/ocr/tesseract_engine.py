from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from backend.config import get_settings


class OcrEngineError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class OcrResult:
    text: str
    page_count: int
    engine: str
    language: str


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


def find_tesseract_command() -> str | None:
    settings = get_settings()
    candidates = [
        settings.tesseract_cmd.strip(),
        shutil.which("tesseract") or "",
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def assert_tesseract_available() -> str:
    command = find_tesseract_command()
    if not command:
        raise OcrEngineError(
            "TESSERACT_NOT_FOUND",
            "Tesseract executable was not found. Install Tesseract OCR and set TESSERACT_CMD if needed.",
        )
    return command


def find_pdftoppm_command() -> str | None:
    candidates = [
        r"C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe",
        shutil.which("pdftoppm") or "",
        r"C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pdftoppm.cmd",
        r"C:\Users\xogns\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\bin\pdftoppm.cmd",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def assert_pdftoppm_available() -> str:
    command = find_pdftoppm_command()
    if not command:
        raise OcrEngineError(
            "PDFTOPPM_NOT_FOUND",
            "Poppler pdftoppm was not found. Install Poppler or add pdftoppm to PATH.",
        )
    return command


def ocr_document(path: Path) -> OcrResult:
    source_path = Path(path)
    if not source_path.exists():
        raise OcrEngineError("FILE_NOT_FOUND", f"OCR source file not found: {source_path}")
    suffix = source_path.suffix.lower()
    if suffix == ".pdf":
        return ocr_pdf(source_path)
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return ocr_image(source_path)
    raise OcrEngineError("UNSUPPORTED_OCR_FILE", f"OCR does not support this file type yet: {suffix}")


def ocr_pdf(path: Path) -> OcrResult:
    settings = get_settings()
    tesseract_command = assert_tesseract_available()
    pdftoppm_command = assert_pdftoppm_available()
    try:
        with tempfile.TemporaryDirectory(prefix="court_ocr_") as tmp_dir:
            output_prefix = str(Path(tmp_dir) / "page")
            converted = subprocess.run(
                [
                    pdftoppm_command,
                    "-r",
                    str(settings.ocr_dpi),
                    "-f",
                    "1",
                    "-l",
                    str(max(1, settings.ocr_max_pages)),
                    "-png",
                    str(path),
                    output_prefix,
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
                check=False,
            )
            if converted.returncode != 0:
                raise OcrEngineError(
                    "PDF_IMAGE_CONVERSION_FAILED",
                    (converted.stderr or converted.stdout or "pdftoppm failed").strip()[:1000],
                )
            image_paths = sorted(Path(tmp_dir).glob("page-*.png"))
            if not image_paths:
                raise OcrEngineError("PDF_IMAGE_CONVERSION_FAILED", "pdftoppm produced no page images")
            text_parts = []
            for image_path in image_paths:
                text_parts.append(_run_tesseract(tesseract_command, image_path, settings.ocr_language))
            return OcrResult(
                text="\n\n".join(text_parts).strip(),
                page_count=len(image_paths),
                engine="tesseract",
                language=settings.ocr_language,
            )
    except OcrEngineError:
        raise
    except Exception as exc:
        raise OcrEngineError("PDF_IMAGE_CONVERSION_FAILED", str(exc)) from exc


def ocr_image(path: Path) -> OcrResult:
    settings = get_settings()
    command = assert_tesseract_available()
    text = _run_tesseract(command, path, settings.ocr_language)
    return OcrResult(text=text.strip(), page_count=1, engine="tesseract", language=settings.ocr_language)


def _run_tesseract(command: str, image_path: Path, language: str) -> str:
    completed = subprocess.run(
        [command, str(image_path), "stdout", "-l", language, "--psm", "6"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    if completed.returncode != 0:
        raise OcrEngineError(
            "TESSERACT_FAILED",
            (completed.stderr or completed.stdout or "Tesseract failed").strip()[:1000],
        )
    return completed.stdout or ""
