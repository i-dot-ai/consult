from abc import ABC, abstractmethod
from typing import List

from consult_ai.models.public_schema import Question, Answer, Theme


class ThemeBackendBase(ABC):
    """
    We need to map a question with answers to a list of themes
    and an updated list of answers which contain a theme id
    """

    @abstractmethod
    def get_themes(
        self, question: Question, answers: List[Answer]
    ) -> tuple[List[Theme], List[Answer]]:
        pass
