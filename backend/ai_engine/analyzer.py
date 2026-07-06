import json
import re
import time
from datetime import date
from typing import Any

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.config import get_settings
from backend.runtime_settings import get_effective_analysis_provider


REQUIRED_KEYS = {
    "main_category",
    "sub_category",
    "address",
    "item_details",
    "min_price",
    "bidding_date",
    "risk_comment",
}
GEMINI_PRIMARY_MODEL = "gemini-1.5-flash-latest"
GEMINI_FALLBACK_MODEL = "gemini-flash-latest"
API_CALL_DELAY_SECONDS = 4


class GeminiAnalysisError(RuntimeError):
    pass


class AiAnalysisProviderError(RuntimeError):
    pass


def is_hallucinated(payload: dict[str, Any]) -> bool:
    return not REQUIRED_KEYS.issubset(payload.keys())


def normalize_main_category(value: Any, sub_category: Any = "") -> str:
    text = f"{value or ''} {sub_category or ''}".strip()
    if "부동산" in text:
        return "부동산"
    if "동산" in text:
        return "동산"
    real_estate_hints = ("아파트", "상가", "토지", "건물", "오피스텔", "주택", "임야", "대지", "부동산", "소재지")
    if any(hint in text for hint in real_estate_hints):
        return "부동산"
    return "동산"


def digits_only_price(value: Any) -> str:
    text = str(value or "0")
    digits = re.sub(r"\D", "", text)
    return digits or "0"


def normalize_bidding_date(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text in {"미정", "없음", "확인 필요", "0"}:
        return "미정"
    match = re.search(r"(20\d{2})[.\-/년\s]+(\d{1,2})[.\-/월\s]+(\d{1,2})", text)
    if not match:
        return "미정"
    year, month, day = match.groups()
    try:
        parsed = date(int(year), int(month), int(day))
    except ValueError:
        return "미정"
    return parsed.isoformat()


def normalize_payload(payload: Any, provider: str = "gemini") -> dict[str, str]:
    if not isinstance(payload, dict):
        raise GeminiAnalysisError("AI returned non-object JSON")
    return {
        "main_category": normalize_main_category(payload.get("main_category"), payload.get("sub_category")),
        "sub_category": str(payload.get("sub_category") or "확인 필요"),
        "address": str(payload.get("address") or "확인 필요"),
        "item_details": str(payload.get("item_details") or "확인 필요"),
        "min_price": digits_only_price(payload.get("min_price")),
        "bidding_date": normalize_bidding_date(payload.get("bidding_date")),
        "risk_comment": str(payload.get("risk_comment") or "확인 필요"),
        "analysis_provider": provider,
    }


def build_prompt(text: str) -> str:
    return (
        "당신은 법원 회생·파산 자산 매각 공고를 분석하는 엔진입니다.\n"
        "추출된 텍스트를 보고 main_category를 반드시 '부동산' 또는 '동산' 중 하나로 분류하세요.\n"
        "반드시 JSON 객체만 반환하세요. 설명, 마크다운, 코드블록은 금지합니다.\n"
        "JSON 스키마는 정확히 다음 키를 포함해야 합니다.\n"
        "{\n"
        '  "main_category": "부동산 또는 동산",\n'
        '  "sub_category": "아파트, 상가, 자동차, 기계 등",\n'
        '  "address": "물건 소재지 또는 보관장소",\n'
        '  "item_details": "부동산은 면적/층수/건물상태 등, 동산은 모델명/연식/주행거리/수량 등 상품의 구체적 팩트 상세 정보 (최대 3문장)",\n'
        '  "min_price": "최저매각가격 (숫자만 추출, 없으면 0)",\n'
        '  "bidding_date": "입찰일 또는 매각기일 (반드시 YYYY-MM-DD 형식으로 변환. 날짜가 없으면 미정)",\n'
        '  "risk_comment": "권리분석 및 주의사항 요약"\n'
        "}\n"
        "추측하지 말고 문서 근거가 부족한 항목은 '확인 필요' 또는 '미정'으로 적으세요.\n\n"
        f"공고 원문:\n{text[:20000]}"
    )


def rate_limit_sleep() -> None:
    time.sleep(API_CALL_DELAY_SECONDS)


def load_json_response(raw_text: str) -> dict[str, Any]:
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def should_try_gemini_fallback(exc: Exception, model_name: str) -> bool:
    message = str(exc).lower()
    return model_name == GEMINI_PRIMARY_MODEL and (
        "not found" in message or "404" in message or "unsupported" in message
    )


def analyze_with_gemini(text: str) -> dict[str, str]:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiAnalysisError("GEMINI_API_KEY is missing")

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        prompt = build_prompt(text)
        response = None
        last_error: Exception | None = None
        for model_name in (GEMINI_PRIMARY_MODEL, GEMINI_FALLBACK_MODEL):
            try:
                rate_limit_sleep()
                model = genai.GenerativeModel(
                    model_name,
                    generation_config={"response_mime_type": "application/json"},
                )
                response = model.generate_content(prompt)
                break
            except Exception as exc:
                last_error = exc
                if not should_try_gemini_fallback(exc, model_name):
                    raise

        if response is None:
            raise GeminiAnalysisError(str(last_error))

        return normalize_payload(load_json_response(response.text), provider="gemini")
    except json.JSONDecodeError as exc:
        raise GeminiAnalysisError("Gemini returned invalid JSON") from exc
    except Exception as exc:
        raise GeminiAnalysisError(str(exc)) from exc


def analyze_with_chatgpt(text: str) -> dict[str, str]:
    settings = get_settings()
    api_key = settings.chatgpt_api_key or settings.openai_api_key
    model_name = settings.chatgpt_model or settings.openai_model
    if not api_key:
        raise AiAnalysisProviderError("CHATGPT_API_KEY is missing")

    try:
        from openai import OpenAI

        rate_limit_sleep()
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=model_name,
            input=build_prompt(text),
        )
        return normalize_payload(load_json_response(response.output_text), provider="chatgpt")
    except json.JSONDecodeError as exc:
        raise AiAnalysisProviderError("ChatGPT returned invalid JSON") from exc
    except Exception as exc:
        raise AiAnalysisProviderError(str(exc)) from exc


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type((GeminiAnalysisError, AiAnalysisProviderError)),
    reraise=True,
)
def analyze_asset_text(text: str) -> dict[str, str]:
    provider = get_effective_analysis_provider()
    if provider in {"chatgpt", "openai"}:
        return analyze_with_chatgpt(text)
    if provider != "gemini":
        raise AiAnalysisProviderError(f"Unsupported ANALYSIS_PROVIDER: {provider}")
    return analyze_with_gemini(text)
