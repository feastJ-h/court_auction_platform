from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketabilityResult:
    score: int
    grade: str
    label: str
    reasons: list[str]


def _safe_int(value: str | None) -> int:
    try:
        return int(value or "0")
    except ValueError:
        return 0


def _days_until(date_text: str | None) -> int | None:
    if not date_text or date_text == "미정":
        return None
    try:
        target = datetime.strptime(date_text, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (target - datetime.now().date()).days


def evaluate_marketability(event) -> MarketabilityResult:
    analysis = event.analyses[0] if event.analyses else None
    score = 60
    reasons: list[str] = []

    if event.status != "AI_ANALYZED":
        score -= 35
        reasons.append("AI 분석 전 상태라 보수적 검토 필요")
    if event.parse_status in {"MANUAL_REVIEW", "PARSE_FAILED"}:
        score -= 25
        reasons.append("문서 텍스트 추출 품질이 낮아 원문 확인 필요")

    if not analysis:
        score -= 25
        reasons.append("최저가와 입찰일이 아직 구조화되지 않음")
    else:
        min_price = _safe_int(analysis.min_price)
        if min_price <= 0:
            score -= 20
            reasons.append("최저매각가격 미확인")
        elif min_price <= 1_000_000:
            score += 8
            reasons.append("소액 물건으로 실험적 검토 가능")

        days = _days_until(analysis.bidding_date)
        if days is None:
            score -= 10
            reasons.append("입찰일 미정")
        elif days < 0:
            score -= 20
            reasons.append("입찰일 경과 가능성")
        elif days <= 7:
            score -= 5
            reasons.append("입찰 임박")
        else:
            score += 5
            reasons.append("검토 시간 확보 가능")

        risk_text = analysis.risk_comment or ""
        if any(keyword in risk_text for keyword in ("확인 필요", "주의", "권리", "등기", "하자")):
            score -= 8
            reasons.append("권리/하자 확인 포인트 존재")

    if event.asset.main_category == "부동산":
        score += 5
        reasons.append("부동산 물건은 시세 비교 확장 가능")
    else:
        score += 2
        reasons.append("동산 물건은 회전성 중심 검토")

    score = max(0, min(100, score))
    if score >= 75:
        return MarketabilityResult(score, "A", "관심", reasons)
    if score >= 50:
        return MarketabilityResult(score, "B", "검토", reasons)
    return MarketabilityResult(score, "C", "보류", reasons)
