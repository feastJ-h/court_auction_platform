import time

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from backend.ai_engine.analyzer import GEMINI_FALLBACK_MODEL, GEMINI_PRIMARY_MODEL, GeminiAnalysisError
from backend.config import get_settings


API_CALL_DELAY_SECONDS = 4


REAL_ESTATE_INSTRUCTIONS = (
    "너는 부동산 권리분석 및 가치평가 전문가다. 원문에서 다음을 심층 분석해라:\n"
    "1) 명도 저항(임차인 등) 및 인수해야 할 숨은 권리(법정지상권, 유치권 등) 리스크\n"
    "2) 토지이용계획이나 지목에 따른 건물 신축/용도변경 가능성\n"
    "3) 인근 지역 시세 추론(문서 내 언급된 감정가 대비)."
)

MOVABLE_ASSET_INSTRUCTIONS = (
    "너는 동산 및 기계/차량 감정 전문가다. 원문에서 다음을 심층 분석해라:\n"
    "1) 연식, 모델명에 따른 감가상각 및 중고 시장 가치 추론\n"
    "2) 보관 장소 이전에 따른 추가 비용(보관료, 지게차 등 이동비용) 리스크\n"
    "3) 훼손 및 부품 결품 가능성."
)


def build_deep_prompt(
    main_category: str,
    raw_text: str,
    item_details: str = "",
    risk_comment: str = "",
) -> str:
    instructions = (
        REAL_ESTATE_INSTRUCTIONS if main_category == "부동산" else MOVABLE_ASSET_INSTRUCTIONS
    )
    return (
        f"{instructions}\n\n"
        "반드시 아래 형식의 한국어 리포트로 작성해라.\n"
        "- 핵심 판단\n"
        "- 주요 리스크\n"
        "- 추가 확인자료\n"
        "- 매입/매각 관점의 결론\n\n"
        "추측은 '추정'이라고 표시하고, 문서에 없는 사실을 확정하지 마라.\n\n"
        f"기본 상품 정보:\n{item_details[:3000]}\n\n"
        f"기본 리스크 요약:\n{risk_comment[:3000]}\n\n"
        f"공고 원문:\n{raw_text[:24000]}"
    )


def should_try_fallback(exc: Exception, model_name: str) -> bool:
    message = str(exc).lower()
    return model_name == GEMINI_PRIMARY_MODEL and (
        "not found" in message or "404" in message or "unsupported" in message
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
    retry=retry_if_exception_type(GeminiAnalysisError),
    reraise=True,
)
def analyze_deep_with_gemini(
    main_category: str,
    raw_text: str,
    item_details: str = "",
    risk_comment: str = "",
) -> str:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiAnalysisError("GEMINI_API_KEY is missing")
    if not raw_text.strip() and not item_details.strip() and not risk_comment.strip():
        raise GeminiAnalysisError("No source text available for deep analysis")

    try:
        import google.generativeai as genai

        genai.configure(api_key=settings.gemini_api_key)
        prompt = build_deep_prompt(main_category, raw_text, item_details, risk_comment)
        last_error: Exception | None = None
        for model_name in (GEMINI_PRIMARY_MODEL, GEMINI_FALLBACK_MODEL):
            try:
                time.sleep(API_CALL_DELAY_SECONDS)
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = (response.text or "").strip()
                if not text:
                    raise GeminiAnalysisError("Gemini returned empty deep analysis")
                return text
            except Exception as exc:
                last_error = exc
                if not should_try_fallback(exc, model_name):
                    raise
        raise GeminiAnalysisError(str(last_error))
    except GeminiAnalysisError:
        raise
    except Exception as exc:
        raise GeminiAnalysisError(str(exc)) from exc
