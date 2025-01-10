"""
Test factories for the new consultation models.
"""

import pytest

from consultation_analyser import factories
from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_factories():
    # Check that each object is created
    user = factories.UserFactory()
    assert User.objects.filter(id=user.id).exists()

    consultation = factories.ConsultationFactory()
    assert models.Consultation.objects.filter(id=consultation.id).exists()

    question = factories.QuestionFactory()
    assert models.Question.objects.filter(id=question.id).exists()
    question_part = factories.QuestionPartFactory()
    assert models.QuestionPart.objects.filter(id=question_part.id).exists()

    respondent = factories.RespondentFactory()
    assert models.Respondent.objects.filter(id=respondent.id).exists()

    answer = factories.AnswerFactory()
    assert models.Answer.objects.filter(id=answer.id).exists()

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
