import os
from unittest.mock import patch

import pytest

from consultation_analyser.consultations import models
from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml


@pytest.mark.django_db
@patch("consultation_analyser.hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_a_consultation_is_generated(settings):
    assert models.Consultation2.objects.count() == 0

    create_dummy_consultation_from_yaml()

    assert models.Consultation2.objects.count() == 1
    assert models.Question2.objects.count() == 5


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod"])
def test_the_tool_will_only_run_in_dev(environment):
    with patch.dict(os.environ, {"ENVIRONMENT": environment}):
        with pytest.raises(
            Exception, match=r"Dummy data generation should not be run in production"
        ):
            create_dummy_consultation_from_yaml()


@pytest.mark.django_db
def test_create_dummy_consultation_from_yaml():
    consultation = create_dummy_consultation_from_yaml(number_respondents=10)
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
    assert themes.filter(name="Standardized framework").exists()

    assert models.QuestionPart.objects.filter(
        type=models.QuestionPart.QuestionType.SINGLE_OPTION
    ).exists()
    assert models.QuestionPart.objects.filter(
        type=models.QuestionPart.QuestionType.MULTIPLE_OPTIONS
    ).exists()

    assert models.ExecutionRun.objects.count() == 3 * 3  # 3 free-text parts, 3 types of run
    assert models.Framework.objects.count() == 3
