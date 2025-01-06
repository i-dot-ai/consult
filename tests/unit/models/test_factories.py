"""
Test factories for the new consultation models.
"""

import pytest

from consultation_analyser import factories


@pytest.mark.django_db
def test_factories():
    # just check nothing fails
    factories.UserFactory()
    factories.ConsultationFactory()
    factories.QuestionFactory()
    factories.QuestionPartFactory()
    factories.RespondentFactory()
    factories.AnswerFactory()
    factories.ExecutionRunFactory()
    factories.FrameworkFactory()
    factories.ThemeFactory()
    factories.ThemeMappingFactory()
    factories.SentimentMappingFactory()
