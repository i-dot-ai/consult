import pytest

from backend import factories
from backend.consultations import models
from backend.factories import QuestionFactory


@pytest.mark.django_db
def test_delete_question(consultation):
    question = QuestionFactory()
    respondent = factories.RespondentFactory(consultation=consultation)
    response = factories.ResponseFactory(question=question, respondent=respondent)
    theme = factories.SelectedThemeFactory(question=question)
    annotation = factories.ResponseAnnotationFactoryNoThemes(response=response)
    annotation.add_original_ai_themes([theme])

    num_respondents = models.Respondent.objects.count()

    assert models.Question.objects.count() == 1
    assert models.Response.objects.count() == 1
    assert models.SelectedTheme.objects.count() == 1
    assert models.ResponseAnnotationTheme.objects.count() == 1

    question.delete()

    assert models.Respondent.objects.count() == num_respondents
    assert models.Question.objects.count() == 0
    assert models.Response.objects.count() == 0
    assert models.SelectedTheme.objects.count() == 0
    assert models.ResponseAnnotationTheme.objects.count() == 0
