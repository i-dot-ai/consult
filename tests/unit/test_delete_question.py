import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_delete_question():
    consultation = factories.ConsultationFactory()
    question = factories.QuestionFactory(consultation=consultation)
    question_part = factories.FreeTextQuestionPartFactory(question=question)
    respondent = factories.RespondentFactory(consultation=consultation)
    answer = factories.FreeTextAnswerFactory(question_part=question_part, respondent=respondent)
    framework = factories.InitialFrameworkFactory(question_part=question_part)
    theme = factories.InitialThemeFactory(framework=framework, key="A")
    factories.ThemeMappingFactory(answer=answer, theme=theme)

    num_respondents = models.Respondent.objects.count()

    assert models.Question.objects.count() == 1
    assert models.QuestionPart.objects.count() == 1
    assert models.Answer.objects.count() == 1
    assert models.Framework.objects.count() == 1
    assert models.Theme.objects.count() == 1
    assert models.ThemeMapping.objects.count() == 1

    question.delete()

    assert models.Respondent.objects.count() == num_respondents
    assert models.Question.objects.count() == 0
    assert models.QuestionPart.objects.count() == 0
    assert models.Answer.objects.count() == 0
    assert models.Framework.objects.count() == 0
    assert models.Theme.objects.count() == 0
    assert models.ThemeMapping.objects.count() == 0
