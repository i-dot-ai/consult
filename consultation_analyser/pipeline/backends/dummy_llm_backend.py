import faker

from consultation_analyser.consultations import models

from .llm_backend import LLMBackend
from .types import ThemeSummary


class DummyLLMBackend(LLMBackend):
    def __init__(self):
        self.faker = faker.Faker()

    def summarise_theme(self, theme: models.OldTheme) -> ThemeSummary:
        return ThemeSummary(
            **{
                "short_description": ", ".join(theme.topic_keywords),
                "summary": self.faker.sentence(),
            }
        )
