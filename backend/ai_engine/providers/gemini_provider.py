from backend.ai_engine.analyzer import analyze_with_gemini
from backend.ai_engine.providers.base import AnalysisProvider


class GeminiProvider(AnalysisProvider):
    name = "gemini"

    def analyze_basic(self, text: str) -> dict[str, str]:
        return analyze_with_gemini(text)
