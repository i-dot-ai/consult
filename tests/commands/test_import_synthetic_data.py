import pytest

from consultation_analyser.consultations.management.commands.import_synthetic_data import Command
from consultation_analyser.consultations.models import (
    Answer,
    QuestionPart,
    SentimentMapping,
    ThemeMapping,
)
from consultation_analyser.factories import (
    ConsultationFactory,
    InitialFrameworkFactory,
    InitialThemeFactory,
    RespondentFactory,
)

# Not testing the full command the file system, as it would be too long for repeated automated tests


@pytest.mark.django_db
def test_get_theme():
    theme_data = {
        "Agreement": {
            "A": {
                "topics": [
                    {"topic_name": "Public Health Benefits"},
                    {"topic_name": "Health Advantages"},
                ]
            },
            "B": {
                "topics": [
                    {"topic_name": "Supporting Responsible Behavior"},
                    {"topic_name": "Encouraging Accountable Conduct"},
                ]
            },
        },
        "Disagreement": {
            "C": {
                "topics": [
                    {"topic_name": "Freedom of Speech"},
                    {"topic_name": "Freedom of Expression"},
                ]
            },
            "D": {
                "topics": [
                    {"topic_name": "Economic Benefits"},
                    {"topic_name": "Financial Advantages"},
                ]
            },
        },
    }

    framework = InitialFrameworkFactory()
    theme_a = InitialThemeFactory(key="A", framework=framework)
    theme_b = InitialThemeFactory(key="B", framework=framework)
    theme_c = InitialThemeFactory(key="C", framework=framework)

    theme_a_response = {"Health Advantages": "text"}
    theme_b_response = {"Supporting Responsible Behavior": "text"}
    theme_c_response = {"Freedom of Expression": "text"}
    no_response = {"No Topic": "text"}

    command = Command()
    assert command.get_theme(theme_data, theme_a_response, framework) == theme_a
    assert command.get_theme(theme_data, theme_b_response, framework) == theme_b
    assert command.get_theme(theme_data, theme_c_response, framework) == theme_c
    assert command.get_theme(theme_data, no_response, framework) is None


@pytest.mark.skip(reason="Doesn't work whilst in the middle of model changes")
@pytest.mark.django_db
def test_import_question():
    command = Command()
    consultation = ConsultationFactory()

    for i in range(5):
        RespondentFactory(consultation=consultation, themefinder_respondent_id=i + 1)

    command.import_question(999, consultation)

    free_text_qp = QuestionPart.objects.get(
        question__consultation=consultation, type=QuestionPart.QuestionType.FREE_TEXT
    )
    multiple_choice_qp = QuestionPart.objects.get(
        question__consultation=consultation, type=QuestionPart.QuestionType.MULTIPLE_OPTIONS
    )

    assert consultation.questionold_set.count() == 1
    assert Answer.objects.filter(question_part=free_text_qp).count() == 3
    assert (
        Answer.objects.filter(question_part=multiple_choice_qp).count() == 1
    )  # Not all respondents have mande a choice

    free_text_answer = Answer.objects.filter(question_part=free_text_qp).first()
    assert ThemeMapping.objects.get(answer=free_text_answer).theme.key == "C"
    assert SentimentMapping.objects.get(answer=free_text_answer).position == "AGREEMENT"

    multiple_choice_answer = Answer.objects.filter(question_part=multiple_choice_qp).first()
    assert multiple_choice_answer.chosen_options == ["Strongly agree"]
