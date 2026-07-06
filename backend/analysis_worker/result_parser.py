import json
import re
from typing import Any

from backend.jobs.status import ERROR_CLI_OUTPUT_INVALID


REQUIRED_KEYS = {
    "summary",
    "asset_type",
    "price_opinion",
    "key_dates",
    "rights_and_legal_risks",
    "physical_or_market_risks",
    "required_follow_up_documents",
    "recommended_action",
    "confidence",
    "markdown_report",
}


class ResultParseError(RuntimeError):
    def __init__(self, message: str, error_code: str = ERROR_CLI_OUTPUT_INVALID) -> None:
        super().__init__(message)
        self.error_code = error_code


def _find_json_object(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ResultParseError("CLI output does not contain a JSON object")
    return cleaned[start : end + 1]


def parse_cli_output(raw_output: str) -> dict[str, Any]:
    try:
        payload = json.loads(_find_json_object(raw_output))
    except json.JSONDecodeError as exc:
        raise ResultParseError(f"CLI output is not valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise ResultParseError("CLI output JSON must be an object")
    missing = REQUIRED_KEYS - set(payload.keys())
    if missing:
        raise ResultParseError(f"CLI output is missing required keys: {sorted(missing)}")
    confidence = str(payload.get("confidence") or "").lower()
    if confidence not in {"low", "medium", "high"}:
        payload["confidence"] = "low"
    return payload


def markdown_from_payload(payload: dict[str, Any]) -> str:
    markdown_report = str(payload.get("markdown_report") or "").strip()
    if markdown_report:
        return markdown_report

    def list_lines(values: Any) -> str:
        if not isinstance(values, list) or not values:
            return "- 확인 필요"
        return "\n".join(f"- {item}" for item in values)

    return (
        f"# 상세 심층 분석\n\n"
        f"## 요약\n{payload.get('summary') or '확인 필요'}\n\n"
        f"## 가격 의견\n{payload.get('price_opinion') or '확인 필요'}\n\n"
        f"## 권리 및 법률 리스크\n{list_lines(payload.get('rights_and_legal_risks'))}\n\n"
        f"## 물리/시장 리스크\n{list_lines(payload.get('physical_or_market_risks'))}\n\n"
        f"## 추가 확인 서류\n{list_lines(payload.get('required_follow_up_documents'))}\n\n"
        f"## 권장 액션\n{payload.get('recommended_action') or '확인 필요'}\n"
    )
