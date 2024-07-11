from abc import ABC, abstractmethod
from typing import Dict

from consultation_analyser.consultations import models

from .types import TopicAssignment


class TopicBackend(ABC):
    @abstractmethod
    def get_topics(
        self, question: models.Question, topic_model_parameters: Dict
    ) -> list[TopicAssignment]:
        pass
