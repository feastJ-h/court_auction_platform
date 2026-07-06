from backend.database.models import AssetEvent


BLOCKED_PARSE_STATUSES = {
    "EMPTY_TEXT": "추출된 텍스트가 비어 있습니다.",
    "OCR_REQUIRED": "OCR 처리가 먼저 필요합니다.",
    "OCR_FAILED": "OCR 처리 실패 상태입니다.",
    "HWP_CONVERSION_REQUIRED": "HWP 변환이 먼저 필요합니다.",
    "HWP_CONVERSION_FAILED": "HWP 변환 실패 상태입니다.",
    "TEXT_EXTRACTION_FAILED": "텍스트 추출 실패 상태입니다.",
    "PARSE_FAILED": "문서 파싱 실패 상태입니다.",
    "MANUAL_REVIEW": "수동 검토가 필요한 문서입니다.",
}


def get_analysis_readiness(event: AssetEvent) -> dict:
    if event.parse_status in BLOCKED_PARSE_STATUSES:
        return {
            "ready": False,
            "reason": BLOCKED_PARSE_STATUSES[event.parse_status],
            "parse_status": event.parse_status,
        }

    analysis = event.analyses[0] if event.analyses else None
    evidence = event.raw_document.evidence if event.raw_document else None
    text_parts = [
        event.extracted_text or "",
        evidence.detail_page_text if evidence else "",
        analysis.item_details if analysis else "",
        analysis.risk_comment if analysis else "",
    ]
    usable_length = sum(len(part.strip()) for part in text_parts)
    if usable_length < 100:
        return {
            "ready": False,
            "reason": "AI 분석에 사용할 원문/근거 텍스트가 부족합니다.",
            "parse_status": event.parse_status,
        }

    return {
        "ready": True,
        "reason": "분석 요청 가능",
        "parse_status": event.parse_status,
    }
