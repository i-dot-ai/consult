import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.pipeline.backends.bertopic import BERTopicBackend
from consultation_analyser.pipeline.ml_pipeline import (
    save_themes_for_processing_run,
)


@pytest.mark.django_db
def test_topic_model_end_to_end(tmp_path):
    consultation_builder = factories.ConsultationBuilder()
    question_free_text = consultation_builder.add_question(text="Do you like wolves?")
    question_no_free_text = consultation_builder.add_question(
        text="No free text here", has_free_text=False
    )

    # identical answers
    for r in range(10):
        consultation_builder.add_answer(
            question_free_text, free_text="I love wolves, they are fluffy and cute"
        )
        consultation_builder.add_answer(question_no_free_text)
        consultation_builder.next_response()

    backend = BERTopicBackend()
    processing_run = factories.ProcessingRunFactory(consultation=consultation_builder.consultation)
    save_themes_for_processing_run(backend, processing_run)

    # all answers should get the same theme
    assert models.Theme.objects.count() == 1

    assert not models.Theme.objects.filter(answer__question=question_no_free_text).exists()
