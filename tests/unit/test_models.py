import pytest
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
