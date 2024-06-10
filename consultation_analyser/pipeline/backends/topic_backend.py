from abc import ABC, abstractmethod

from consultation_analyser.consultations import models

from .types import TopicAssignment


class TopicBackend(ABC):
    @abstractmethod
    def get_topics(self, question: models.Question) -> list[TopicAssignment]:
        pass

    @abstractmethod
    def save_topic_model(self, output_dir):
        pass

