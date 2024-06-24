import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.parametrize(
    "input_keywords,topic_id,is_outlier",
    [(["key", "lock"], 2, False), (["dog", "cat"], -1, True)],
)
@pytest.mark.django_db
def test_save_theme_to_answer(input_keywords, topic_id, is_outlier):
    consultation = factories.ConsultationFactory()
    consultation_response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(has_free_text=True, section=section)
    answer = factories.AnswerFactory(
        question=question, consultation_response=consultation_response
    )
    processing_run = factories.ProcessingRunFactory(consultation=consultation)
    tm = factories.TopicModelMetadataFactory(processing_run=processing_run, question=question)
    # Check theme created and saved to answer
    answer.save_theme_to_answer(topic_keywords=input_keywords, topic_id=topic_id, topic_model_metadata=tm)
    theme = models.Theme.objects.get(topic_keywords=input_keywords)
    assert theme.topic_keywords == input_keywords
    assert theme.is_outlier == is_outlier
    assert theme in answer.theme.all()
    # Check no duplicate created
    answer.save_theme_to_answer(topic_keywords=input_keywords, topic_id=topic_id, topic_model_metadata=tm)
    themes_qs = models.Theme.objects.filter(topic_keywords=input_keywords)
    assert themes_qs.count() == 1


@pytest.mark.django_db
def test_uniqueness_consultation_slugs():
    factories.ConsultationFactory(name="My new consultation", slug="my-new-consultation")
    with pytest.raises(IntegrityError):
        factories.ConsultationFactory(name="My new consultation 2", slug="my-new-consultation")


@pytest.mark.django_db
def test_multiple_choice_validation():
    question = factories.QuestionFactory()
    resp = factories.ConsultationResponseFactory(consultation=question.section.consultation)
    a = factories.AnswerFactory(question=question, consultation_response=resp)

    a.multiple_choice = {"totally": "invalid"}

    with pytest.raises(ValidationError):
        a.full_clean()


@pytest.mark.django_db
def test_find_answer_multiple_choice_response():
    q = factories.QuestionFactory(
        multiple_choice_questions=[("Do you agree?", ["Yes", "No", "Maybe"])]
    )
    resp = factories.ConsultationResponseFactory(consultation=q.section.consultation)

    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["Yes"])]
    )
    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["No"])]
    )
    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["No"])]
    )

    result = models.Answer.objects.filter_multiple_choice(question="Not a question", answer="Yes")

    assert not result

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="wrong")

    assert not result

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="Yes")

    assert result.count() == 1

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="No")

    assert result.count() == 2


@pytest.mark.django_db
def test_latest_themes_for_question():
    question = factories.QuestionFactory(has_free_text=True)
    consultation = question.section.consultation
    assert not question.latest_themes

    processing_run1 = factories.ProcessingRunFactory(consultation=consultation)
    tm1 = factories.TopicModelMetadataFactory(processing_run=processing_run1, question=question)
    theme1 = factories.ThemeFactory(topic_model_metadata=tm1)
    processing_run2 = factories.ProcessingRunFactory(consultation=consultation)
    tm2 = factories.TopicModelMetadataFactory(processing_run=processing_run2, question=question)
    theme2 = factories.ThemeFactory(topic_model_metadata=tm2)

    assert theme2 in question.latest_themes
    assert theme1 not in question.latest_themes


@pytest.mark.django_db
def test_latest_themes_for_answer():
    question = factories.QuestionFactory(has_free_text=True)
    consultation = question.section.consultation
    response = factories.ConsultationResponseFactory(consultation=consultation)
    answer = factories.AnswerFactory(question=question, consultation_response=response)
    assert not answer.latest_theme

    processing_run1 = factories.ProcessingRunFactory(consultation=consultation)
    tm1 = factories.TopicModelMetadataFactory(processing_run=processing_run1, question=question)
    theme1 = factories.ThemeFactory(topic_model_metadata=tm1)
    answer.theme.add(theme1)
    processing_run2 = factories.ProcessingRunFactory(consultation=consultation)
    tm2 = factories.TopicModelMetadataFactory(processing_run=processing_run2, question=question)
    theme2 = factories.ThemeFactory(topic_model_metadata=tm2)
    answer.theme.add(theme2)

    assert theme2 in question.latest_themes
    assert theme1 not in question.latest_themes


