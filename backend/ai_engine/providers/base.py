from abc import ABC, abstractmethod


class AnalysisProvider(ABC):
    name: str

    @abstractmethod
    def analyze_basic(self, text: str) -> dict[str, str]:
        raise NotImplementedError
