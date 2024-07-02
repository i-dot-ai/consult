import logging
import json

from django.core.serializers.json import DjangoJSONEncoder

from consultation_analyser.consultations import models

from .backends.topic_backend import TopicBackend
from .backends.types import TopicAssignment

logger = logging.getLogger("pipeline")


def topic_assignment_to_dict(assignment: TopicAssignment) -> dict:
    output = {}
    output["answer_id"] = str(assignment.answer.id)
    output["answer_free_text"] = assignment.answer.free_text
    output["topic_id"] = assignment.topic_id # noqa (TODO - sort out mypy)
    output["x_coordinate"] = assignment.x_coordinate # noqa (TODO - sort out mypy)
    output["y_coordinate"] = assignment.y_coordinate # noqa (TODO - sort out mypy)
    # TODO - what else do we want here?
    return output


def save_themes_for_question(
    question: models.Question, topic_backend: TopicBackend, processing_run: models.ProcessingRun
) -> None:
    logging.info(f"Get topics for question: {question.text}")

    assignments = topic_backend.get_topics(question)
    scatter_plot_data = [topic_assignment_to_dict(assignment) for assignment in assignments]
    # # TODO - is this right? This just gives us a big string
    # encoded_scatter_plot_data = json.dumps(scatter_plot_data, cls=DjangoJSONEncoder)
    topic_model_metadata = models.TopicModelMetadata(scatter_plot_data=scatter_plot_data)
    topic_model_metadata.save()
    # TODO - add more metadata to the topic model

    for assignment in assignments:
        assignment.answer.save_theme_to_answer(
            topic_keywords=assignment.topic_keywords,
            topic_id=assignment.topic_id,
            processing_run=processing_run,
            topic_model_metadata=topic_model_metadata,
        )




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
