import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.pipeline.backends.dummy_llm_backend import DummyLLMBackend
from consultation_analyser.pipeline.backends.dummy_topic_backend import DummyTopicBackend
from consultation_analyser.pipeline.processing import process_consultation_themes


@pytest.mark.django_db
def test_latest_processing_run():
    consultation = factories.ConsultationWithAnswersFactory()
    answer = models.Answer.objects.last()

    run1 = process_consultation_themes(consultation, DummyTopicBackend(), DummyLLMBackend())
    run2 = process_consultation_themes(consultation, DummyTopicBackend(), DummyLLMBackend())

    latest_theme_for_answer = consultation.latest_processing_run.get_themes_for_answer(
        answer.id
    ).last()

    assert latest_theme_for_answer == run2.get_themes_for_answer(answer.id).last()
    assert latest_theme_for_answer != run1.get_themes_for_answer(answer.id).last()
