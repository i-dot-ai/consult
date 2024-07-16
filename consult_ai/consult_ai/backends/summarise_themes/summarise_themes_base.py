from abc import ABC, abstractmethod
from typing import List

from consult_ai.models.public_schema import Theme, Answer


class SummariseThemesBase(ABC):
    """We take a theme, and create a summary and description for it"""

    @abstractmethod
    def summarise_theme(
        self,
        theme: Theme,
        sample_responses: List[Answer],
        consultation_name: str,
        question: str,
    ) -> Theme:
        pass
