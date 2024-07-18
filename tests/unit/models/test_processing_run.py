import datetime

import pytest

from django.db import IntegrityError

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
    assert run1.started_at < run1.finished_at


@pytest.mark.django_db
def test_processing_run_slug():
    consultation = factories.ConsultationWithAnswersFactory()

    pr1 = factories.ProcessingRunFactory(consultation=consultation)
    pr2 = factories.ProcessingRunFactory(consultation=consultation)

    # Check slugs unique
    slug1 = pr1.slug
    slug2 = pr2.slug
    assert slug1 != slug2

    # Check all fields saved, slug doesn't change
    pr2.started_at = datetime.datetime(2024, 6, 1, 10, 30, 0)
    pr2.finished_at = datetime.datetime(2024, 6, 1, 11, 30, 0)
    pr2.save()
    assert pr2.started_at == datetime.datetime(2024, 6, 1, 10, 30, 0)
    assert pr2.finished_at == datetime.datetime(2024, 6, 1, 11, 30, 0)
    assert pr2.slug == slug2

    # Check can't have duplicate slugs
    with pytest.raises(IntegrityError):
        pr2.slug = slug1
        pr2.save()



