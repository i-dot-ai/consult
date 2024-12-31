"""
Test factories for the new consultation models.
"""

import pytest

from consultation_analyser import factories2


@pytest.mark.django_db
def test_factories():
    # just check nothing fails
    factories2.UserFactory()
    factories2.Consultation2Factory()
    factories2.QuestionGroupFactory()
    factories2.Question2Factory()
    factories2.QuestionPartFactory()
    factories2.ExpandedQuestionFactory()
    factories2.RespondentFactory()
    factories2.Answer2Factory()
    factories2.ExecutionRunFactory()
    factories2.FrameworkFactory()
    factories2.Theme2Factory()
    factories2.ThemeMappingFactory()
    factories2.SentimentMappingFactory()
