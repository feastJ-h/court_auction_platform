import json
from typing import Any


FINAL_EVENT_TYPES = {"turn/completed", "turn/failed", "error"}


def event_type(event: dict[str, Any]) -> str:
    return str(event.get("method") or event.get("type") or event.get("event") or "unknown")


def event_message(event: dict[str, Any]) -> str:
    params = event.get("params") if isinstance(event.get("params"), dict) else event
    candidates = [
        params.get("message") if isinstance(params, dict) else None,
        params.get("text") if isinstance(params, dict) else None,
        params.get("delta") if isinstance(params, dict) else None,
        params.get("status") if isinstance(params, dict) else None,
    ]
    for candidate in candidates:
        if candidate:
            return str(candidate)
    return event_type(event)


def extract_turn_id(event: dict[str, Any]) -> str:
    params = event.get("params") if isinstance(event.get("params"), dict) else event
    if not isinstance(params, dict):
        return ""
    return str(params.get("turnId") or params.get("turn_id") or params.get("id") or "")


def extract_final_text(event: dict[str, Any]) -> str:
    params = event.get("params") if isinstance(event.get("params"), dict) else event
    if not isinstance(params, dict):
        return ""

    for key in ("finalMessage", "message", "text", "output", "content"):
        value = params.get(key)
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, dict):
            nested = value.get("text") or value.get("content")
            if isinstance(nested, str) and nested.strip():
                return nested
    return ""


def compact_payload(event: dict[str, Any], max_chars: int = 8000) -> str:
    text = json.dumps(event, ensure_ascii=False)
    return text[:max_chars]
