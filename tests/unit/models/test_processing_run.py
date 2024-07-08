import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


def set_up_consultation():
    consultation = factories.ConsultationFactory()
    consultation_response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(section=section, text="Question 1?")
    answer = factories.AnswerFactory(
        question=question, consultation_response=consultation_response, free_text="Answer 1"
    )
    for i in range(3):
        processing_run = factories.ProcessingRunFactory(consultation=consultation)
        theme = factories.ThemeFactory(
            processing_run=processing_run, short_description=f"Theme {i}"
        )
        answer.themes.add(theme)
    return consultation


@pytest.mark.django_db
def test_latest_processing_run():
    consultation1 = factories.ConsultationFactory()
    assert not consultation1.latest_processing_run
    consultation2 = set_up_consultation()
    answer = models.Answer.objects.get(free_text="Answer 1")
    question = models.Question.objects.get(text="Question 1?")
    latest_run = consultation2.latest_processing_run
    assert latest_run
    themes = latest_run.get_themes_for_answer(answer.id)
    assert themes.last().short_description == "Theme 2"
    assert "Theme 0" not in themes.values_list("short_description", flat=True)
    themes = latest_run.get_themes_for_question(question.id)
    assert themes.count() == 1  # Ensure distinct
    assert themes.last().short_description == "Theme 2"
