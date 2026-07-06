import json

from backend.config import PROJECT_ROOT, get_settings


RUNTIME_SETTINGS_PATH = PROJECT_ROOT / "runtime_settings.json"
SUPPORTED_ANALYSIS_PROVIDERS = {"gemini", "chatgpt", "openai"}


def read_runtime_settings() -> dict[str, str]:
    if not RUNTIME_SETTINGS_PATH.exists():
        return {"analysis_provider": get_settings().analysis_provider}
    try:
        data = json.loads(RUNTIME_SETTINGS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"analysis_provider": get_settings().analysis_provider}
    provider = str(data.get("analysis_provider") or get_settings().analysis_provider).lower()
    if provider not in SUPPORTED_ANALYSIS_PROVIDERS:
        provider = "chatgpt"
    return {"analysis_provider": provider}


def write_analysis_provider(provider: str) -> str:
    normalized = provider.strip().lower()
    if normalized not in SUPPORTED_ANALYSIS_PROVIDERS:
        raise ValueError(f"Unsupported analysis provider: {provider}")
    RUNTIME_SETTINGS_PATH.write_text(
        json.dumps({"analysis_provider": normalized}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return normalized


def get_effective_analysis_provider() -> str:
    return read_runtime_settings()["analysis_provider"]
