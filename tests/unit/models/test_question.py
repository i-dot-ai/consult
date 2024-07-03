import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.django_db
def test_get_multiple_choice_counts():
    consultation = factories.ConsultationFactory()
    section = factories.SectionFactory()
    question = factories.QuestionFactory(
        section=section, multiple_choice_questions=[("What do you like?", ["Rain", "Sun", "Snow"])]
    )

    for a in [
            ["Rain"],
            ["Rain"],
            ["Rain"],
            ["Sun"],
            ["Sun"],
            ["Snow"],
            ["Rain", "Sun"],
            ["Sun", "Snow"]]:
        factories.AnswerFactory(
            multiple_choice_answers=[("What do you like?", a)],
            question=question,
            consultation_response=factories.ConsultationResponseFactory(consultation=consultation),
        )

    result = question.multiple_choice_counts('What do you like?')
    sorted_result = sorted(result, key=lambda r: r["option"])

    assert sorted_result[0] == {"option": "Rain", "count": 4}
    assert sorted_result[1] == {"option": "Snow", "count": 2}
    assert sorted_result[2] == {"option": "Sun", "count": 4}

