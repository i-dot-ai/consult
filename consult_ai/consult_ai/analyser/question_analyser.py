from pydantic import BaseModel
from typing import List, Optional
from random import sample

from consult_ai.models.public_schema import Question, Answer, Theme
from consult_ai.backends.theme.theme_backend_base import ThemeBackendBase
from consult_ai.backends.summarise_themes.summarise_themes_base import (
    SummariseThemesBase,
)


class QuestionAnalyser(BaseModel):
    """
    This Question Analyser class is how we take our
    input questions and answers and pass them through
    different backends
    """

    consultation_name: str
    question: Question
    answers: List[Answer]
    themes: Optional[List[Theme]] = None

    def get_themes(self, theme_backend: ThemeBackendBase):
        themes, answers = theme_backend.get_themes(self.question, self.answers)
        self.themes = themes
        self.answers = answers

    def summarise_themes(
        self, summarise_theme_backend: SummariseThemesBase, size_sample_answers: int = 3
    ):
        consultation_name = self.consultation_name
        question = self.question.text
        for theme in self.themes:
            theme_responses = [
                answer for answer in self.answers if answer.theme_id == theme.id
            ]
            sample_responses = sample(theme_responses, size_sample_answers)
            self.theme = summarise_theme_backend.summarise_theme(
                theme=theme,
                sample_responses=sample_responses,
                consultation_name=consultation_name,
                question=question,
            )
