"""
Test factories for the new consultation models.
"""

import pytest

from consultation_analyser import factories
from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_factories():
    # Basic check that each object is created
    user = factories.UserFactory()
    assert User.objects.filter(id=user.id).exists()

    consultation = factories.ConsultationFactory()
    assert models.Consultation.objects.filter(id=consultation.id).exists()

    question = factories.QuestionFactory()
    assert models.Question.objects.filter(id=question.id).exists()
    question_part = factories.FreeTextQuestionPartFactory()
    assert models.QuestionPart.objects.filter(id=question_part.id).exists()
    assert question_part.type == models.QuestionPart.QuestionType.FREE_TEXT
    assert not question_part.options
    question_part = factories.SingleOptionQuestionPartFactory()
    assert models.QuestionPart.objects.filter(id=question_part.id).exists()
    assert question_part.type == models.QuestionPart.QuestionType.SINGLE_OPTION
    assert question_part.options
    question_part = factories.MultipleOptionQuestionPartFactory()
    assert models.QuestionPart.objects.filter(id=question_part.id).exists()
    assert question_part.type == models.QuestionPart.QuestionType.MULTIPLE_OPTIONS
    assert question_part.options

    respondent = factories.RespondentFactory()
    assert models.Respondent.objects.filter(id=respondent.id).exists()

    answer = factories.FreeTextAnswerFactory()
    assert models.Answer.objects.filter(id=answer.id).exists()
    assert answer.question_part.type == models.QuestionPart.QuestionType.FREE_TEXT
    answer = factories.SingleOptionAnswerFactory()
    assert answer.question_part.type == models.QuestionPart.QuestionType.SINGLE_OPTION
    answer = factories.MultipleOptionAnswerFactory()
    assert answer.question_part.type == models.QuestionPart.QuestionType.MULTIPLE_OPTIONS

    run = factories.ExecutionRunFactory()
    assert models.ExecutionRun.objects.filter(id=run.id).exists()

    framework = factories.InitialFrameworkFactory()
    assert models.Framework.objects.filter(id=framework.id).exists()
    framework = factories.DescendantFrameworkFactory()
    assert models.Framework.objects.filter(id=framework.id).exists()

    theme = factories.InitialThemeFactory()
    assert models.Theme.objects.filter(id=theme.id).exists()
    theme = factories.DescendantThemeFactory()
    assert models.Theme.objects.filter(id=theme.id).exists()
    mapping = factories.ThemeMappingFactory()
    assert models.ThemeMapping.objects.filter(id=mapping.id).exists()

    sentiment_mapping = factories.SentimentMappingFactory()
    assert models.SentimentMapping.objects.filter(id=sentiment_mapping.id).exists()
