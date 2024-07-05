import logging
import random

from faker import Faker

from consultation_analyser.consultations import models

from .topic_backend import TopicBackend
from .types import TopicAssignment

logger = logging.getLogger("pipeline")


def random_partition(lst):
    result = []
    current_sublist = []

    for item in lst:
        if current_sublist and random.random() < 0.25:
            result.append(current_sublist)
            current_sublist = []
        current_sublist.append(item)

    if current_sublist:
        result.append(current_sublist)

    return result


class DummyTopicBackend(TopicBackend):
    def get_topics(self, question: models.Question) -> list[TopicAssignment]:
        faker = Faker()
        answers = models.Answer.objects.filter(question=question).order_by("created_at")

        assignments = []
        topic_id = -1

        # introduce some clumping in the topics
        for answer_set in random_partition(answers):
            topic_keywords = faker.words(4)
            for answer in answer_set:
                assignments.append(
                    TopicAssignment(topic_id=topic_id, topic_keywords=topic_keywords, answer=answer)
                )

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
