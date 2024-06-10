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
            assignments.append(
                TopicAssignment(topic_id=topic_id, topic_keywords=topic_keywords, answer=answer)
            )
            topic_id += 1

        return assignments

    def save_topic_model(self, output_dir) -> None:
        f = open(output_dir / "GENERATED_WITH_DUMMY_TOPIC_MODEL.txt", "w")
        f.write("This output was generated with a dummy topic model")
        f.close()

