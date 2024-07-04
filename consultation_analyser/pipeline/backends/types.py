from dataclasses import dataclass

from pydantic import BaseModel

from consultation_analyser.consultations import models

NO_SUMMARY_STR = "Unable to generate summary for this theme"


@dataclass
class TopicAssignment:
    topic_id: int
    topic_keywords: list[str]
    answer: models.Answer
    x_coordinate: float
    y_coordinate: float


class ThemeSummary(BaseModel):
    summary: str
    short_description: str
