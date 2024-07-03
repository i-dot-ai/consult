import pytest

from consultation_analyser import factories


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
        ["Sun", "Snow"],
    ]:
        factories.AnswerFactory(
            multiple_choice_answers=[("What do you like?", a)],
            question=question,
            consultation_response=factories.ConsultationResponseFactory(consultation=consultation),
        )

    result = question.multiple_choice_stats()

    assert len(result) == 1

    stats = result[0]

    assert stats.question == "What do you like?"
    assert stats.counts["Rain"] == 4
    assert stats.counts["Snow"] == 2
    assert stats.counts["Sun"] == 4

    assert stats.percentages["Rain"] == 40
    assert stats.percentages["Snow"] == 20
    assert stats.percentages["Sun"] == 40
