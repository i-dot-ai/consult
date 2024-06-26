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
    answer = factories.AnswerFactory(question=question, consultation_response=consultation_response)
    processing_run = factories.ProcessingRunFactory(consultation=consultation)
    topic_model_meta = factories.TopicModelMetadataFactory()
    #  Check theme created and saved to answer
    answer.save_theme_to_answer(
        topic_keywords=input_keywords,
        topic_id=topic_id,
        processing_run=processing_run,
        topic_model_metadata=topic_model_meta,
    )
    theme = models.Theme.objects.get(topic_keywords=input_keywords)
    assert theme.topic_keywords == input_keywords
    assert theme.is_outlier == is_outlier
    assert answer.latest_theme.topic_keywords == input_keywords
    # Check no duplicate created
    answer.save_theme_to_answer(
        topic_keywords=input_keywords,
        topic_id=topic_id,
        processing_run=processing_run,
        topic_model_metadata=topic_model_meta,
    )
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


def set_up_question():
    consultation = factories.ConsultationFactory()
    consultation_response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(section=section)
    for i in range(3):
        factories.AnswerFactory(consultation_response=consultation_response, question=question)
    return question


def dummy_ml_run(question):
    topic_model_meta = factories.TopicModelMetadataFactory()
    processing_run = factories.ProcessingRunFactory(consultation=question.section.consultation)
    theme = factories.ThemeFactory(
        topic_model_metadata=topic_model_meta, processing_run=processing_run
    )
    for answer in question.answer_set.all():
        answer.themes.add(theme)
    return theme


@pytest.mark.django_db
def test_question_get_latest_themes():
    question = set_up_question()
    first_theme = dummy_ml_run(question)
    second_theme = dummy_ml_run(question)
    last_theme = dummy_ml_run(question)
    assert question.latest_themes.count() == 1
    assert last_theme in question.latest_themes
    assert first_theme not in question.latest_themes
    assert second_theme not in question.latest_themes


@pytest.mark.django_db
def test_answer_get_latest_themes():
    question = set_up_question()
    first_theme = dummy_ml_run(question)
    last_theme = dummy_ml_run(question)
    answer = question.answer_set.first()
    assert answer.latest_theme == last_theme
    assert answer.latest_theme != first_theme
