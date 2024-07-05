import logging

from faker import Faker

from consultation_analyser.consultations import models

from .topic_backend import TopicBackend
from .types import TopicAssignment

logger = logging.getLogger("django.server")


class DummyTopicBackend(TopicBackend):
    def get_topics(self, question: models.Question) -> list[TopicAssignment]:
        faker = Faker()
        answers = models.Answer.objects.filter(question=question).order_by("created_at")

        assignments = []
        topic_id = -1
        for answer in answers:
            topic_keywords = faker.words(4)
            x_coordinate = faker.pyfloat()
            y_coordinate = faker.pyfloat()
            assignments.append(
                TopicAssignment(
                    topic_id=topic_id,
                    topic_keywords=topic_keywords,
                    answer=answer,
                    x_coordinate=x_coordinate,
                    y_coordinate=y_coordinate,
                )
            )
            topic_id += 1

        return assignments
