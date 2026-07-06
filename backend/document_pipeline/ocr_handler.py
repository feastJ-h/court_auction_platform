class OcrRequiredError(RuntimeError):
    pass


def run_ocr_placeholder(file_path: str) -> str:
    raise OcrRequiredError(f"OCR pipeline is not configured yet: {file_path}")
