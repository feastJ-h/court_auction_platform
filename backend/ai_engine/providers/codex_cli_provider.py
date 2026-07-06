from backend.ai_engine.providers.base import AnalysisProvider


class CodexCliProvider(AnalysisProvider):
    name = "codex_cli"

    def analyze_basic(self, text: str) -> dict[str, str]:
        raise NotImplementedError("Codex CLI provider is used through asynchronous analysis_jobs.")
