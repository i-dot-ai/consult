import logging
from uuid import UUID

from consultation_analyser.consultations import models

from .backends.topic_backend import TopicBackend

logger = logging.getLogger("pipeline")


def save_themes_for_question(question: models.Question, topic_backend: TopicBackend) -> None:
    logging.info(f"Get topics for question: {question.text}")
    assignments = topic_backend.get_topics(question)

    for assignment in assignments:
        assignment.answer.save_theme_to_answer(
            topic_keywords=assignment.topic_keywords, topic_id=assignment.topic_id
        )


def save_themes_for_consultation(consultation_id: UUID, topic_backend: TopicBackend) -> None:
    logging.info(f"Starting topic modelling for consultation_id: {consultation_id}")
    questions = models.Question.objects.filter(
        section__consultation__id=consultation_id, has_free_text=True
    )

    for question in questions:
        save_themes_for_question(question, topic_backend=topic_backend)
