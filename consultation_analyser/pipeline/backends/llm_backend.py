from abc import ABC, abstractmethod

from consultation_analyser.consultations import models

from .types import ThemeSummary


class LLMBackend(ABC):
    @abstractmethod
    def summarise_theme(self, theme: models.Theme) -> ThemeSummary:
        pass
