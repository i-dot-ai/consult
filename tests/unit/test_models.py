import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.parametrize("input_keywords,is_outlier", [(["key", "lock"], False), (["dog", "cat"], True)])
@pytest.mark.django_db
def test_save_theme_to_answer(input_keywords, is_outlier):
    consultation = factories.ConsultationFactory()
    consultation_response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(has_free_text=True, section=section)
    answer = factories.AnswerFactory(question=question, theme=None, consultation_response=consultation_response)
    # Check theme created and saved to answer
    answer.save_theme_to_answer(keywords=input_keywords, is_outlier=is_outlier)
    theme = models.Theme.objects.get(keywords=input_keywords)
    assert theme.keywords == input_keywords
    assert theme.is_outlier == is_outlier
    assert answer.theme.keywords == input_keywords
    # Check no duplicate created
    answer.save_theme_to_answer(keywords=input_keywords, is_outlier=is_outlier)
    themes_qs = models.Theme.objects.filter(keywords=input_keywords, question=question)
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
    q = factories.QuestionFactory(multiple_choice_questions=[("Do you agree?", ["Yes", "No", "Maybe"])])
    resp = factories.ConsultationResponseFactory(consultation=q.section.consultation)

    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["Yes"])]
    )
    factories.AnswerFactory(question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["No"])])
    factories.AnswerFactory(question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["No"])])

    result = models.Answer.objects.filter_multiple_choice(question="Not a question", answer="Yes")

    assert not result

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="wrong")

    assert not result

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="Yes")

    assert result.count() == 1

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="No")

    assert result.count() == 2
