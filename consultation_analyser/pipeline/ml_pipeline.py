import logging

from consultation_analyser.consultations import models

from .backends.topic_backend import TopicBackend
from .backends.types import TopicAssignment

logger = logging.getLogger("pipeline")


def topic_assignment_to_dict(assignment: TopicAssignment) -> dict[str, str | int | float]:
    output = {
        "answer_id": str(assignment.answer.id),
        "answer_free_text": assignment.answer.free_text,
        "topic_id": assignment.topic_id,
        "x_coordinate": assignment.x_coordinate,
        "y_coordinate": assignment.y_coordinate,
    }
    return output


def save_themes_for_question(
    question: models.Question,
    topic_backend: TopicBackend,
    processing_run: models.ProcessingRun,
) -> None:
    logging.info(f"Get topics for question: {question.text}")
    topic_model_metadata = models.TopicModelMetadata()
    topic_model_metadata.save()
    # TODO - add more metadata to the topic model
    assignments = topic_backend.get_topics(question)

    for assignment in assignments:
        assignment.answer.save_theme_to_answer(
            topic_keywords=assignment.topic_keywords,
            topic_id=assignment.topic_id,
            processing_run=processing_run,
            topic_model_metadata=topic_model_metadata,
        )

    # scatter_plot_data = [topic_assignment_to_dict(assignment) for assignment in assignments]
    # TODO - save to topic metadata


def save_themes_for_processing_run(
    topic_backend: TopicBackend, processing_run: models.ProcessingRun
) -> None:
    consultation = processing_run.consultation
    logging.info(f"Starting topic modelling for consultation: {consultation.name}")
    questions = models.Question.objects.filter(
        section__consultation=consultation, has_free_text=True
    )

    for question in questions:
        save_themes_for_question(
            question, topic_backend=topic_backend, processing_run=processing_run
        )
