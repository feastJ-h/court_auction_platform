from backend.ai_engine.analyzer import analyze_with_chatgpt
from backend.ai_engine.providers.base import AnalysisProvider


class OpenAiProvider(AnalysisProvider):
    name = "chatgpt"

    def analyze_basic(self, text: str) -> dict[str, str]:
        return analyze_with_chatgpt(text)
