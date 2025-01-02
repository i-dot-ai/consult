"""
Test factories for the new consultation models.
"""

import pytest

from consultation_analyser import factories2
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_factories():
    # just check nothing fails
    factories2.UserFactory()
    factories2.Consultation2Factory()
    factories2.Question2Factory()
    factories2.QuestionPartFactory()
    factories2.RespondentFactory()
    factories2.Answer2Factory()
    factories2.ExecutionRunFactory()
    factories2.FrameworkFactory()
    factories2.Theme2Factory()
    factories2.ThemeMappingFactory()
    factories2.SentimentMappingFactory()


@pytest.mark.django_db
def test_create_dummy_consultation_from_yaml():
    consultation = factories2.create_dummy_consultation_from_yaml(number_respondents=10)
    questions = models.Question2.objects.filter(consultation=consultation)
    assert questions.count() == 5
    assert questions.filter(
        text="What are your thoughts on how the current chocolate bar regulations could be improved to better address consumer needs and industry standards?"
    ).exists()

    question_1 = questions.get(
        text="Do you agree with the proposal to align the flavour categories of chocolate bars as outlined in the draft guidelines of the Chocolate Bar Regulation for the United Kingdom?"
    )
    question_parts = models.QuestionPart.objects.filter(question=question_1).order_by("order")
    assert question_parts[0].type == models.QuestionPart.QuestionType.SINGLE_OPTION
    assert question_parts[0].options == ["Yes", "No", "Don't know", "No answer"]
    assert question_parts[0].order == 1
    assert not question_parts[0].text
    assert question_parts[1].text == "Please explain your answer."
    assert not question_parts[1].options
    answers = models.Answer2.objects.filter(question_part=question_parts[1])
    assert answers.count() == 10
    theme_mapping = models.ThemeMapping.objects.filter(answer__in=answers)
    assert theme_mapping.count() >= 10
    themes = models.Theme2.objects.filter(framework__question_part=question_parts[1])
    assert themes.count() == 2
    assert themes.filter(theme_name="Standardized framework").exists()

    assert models.QuestionPart.objects.filter(
        type=models.QuestionPart.QuestionType.SINGLE_OPTION
    ).exists()
    assert models.QuestionPart.objects.filter(
        type=models.QuestionPart.QuestionType.MULTIPLE_OPTIONS
    ).exists()

    assert models.ExecutionRun.objects.count() == 3 * 3  # 3 free-text parts, 3 types of run
    assert models.Framework.objects.count() == 3
