import logging
from uuid import UUID

from django.conf import settings

from consultation_analyser.consultations import models
from .backends.topic_backend import TopicBackend
from .backends.bertopic import BERTopicBackend

logger = logging.getLogger("django.server")


def save_themes_for_question(question: models.Question, topic_backend: TopicBackend) -> None:
    logging.info(f"Get topics for question: {question.text}")
    assignments = topic_backend.get_topics(question)
    for assignment in assignments:
        assignment.answer.save_theme_to_answer(
            topic_keywords=assignment.topic_keywords, topic_id=assignment.topic_id
        )

    # if embedding_model_name == "fake":
    #     from faker import Faker
    #     import random
    #
    #     f = Faker()
    #     n_themes_for_question = random.randint(4, 8)
    #     for i, answer in enumerate(answers_qs):
    #         answer.save_theme_to_answer(topic_keywords=f.words(4), topic_id=i)
    #     return


def save_themes_for_consultation(
    consultation_id: UUID, embedding_model_name=settings.BERTOPIC_DEFAULT_EMBEDDING_MODEL
) -> None:
    logging.info(f"Starting topic modelling for consultation_id: {consultation_id}")
    questions = models.Question.objects.filter(
        section__consultation__id=consultation_id, has_free_text=True
    )

    topic_backend = BERTopicBackend(embedding_model=embedding_model_name)
    for question in questions:
        save_themes_for_question(question, topic_backend=topic_backend)
