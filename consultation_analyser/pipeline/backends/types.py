from dataclasses import dataclass

from consultation_analyser.consultations import models


@dataclass
class TopicAssignment:
    topic_id: int
    topic_keywords: list[str]
    answer: models.Answer
