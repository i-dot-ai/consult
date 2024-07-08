import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import MultipleChoiceNotProportionalError


@pytest.mark.django_db
def test_get_multiple_choice_stats():
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

    assert stats.has_multiple_selections

    with pytest.raises(MultipleChoiceNotProportionalError):
        stats.percentages()


@pytest.mark.django_db
def test_get_multiple_choice_has_multiple_selections():
    consultation = factories.ConsultationFactory()
    section = factories.SectionFactory()
    question = factories.QuestionFactory(
        section=section, multiple_choice_questions=[("What do you like?", ["Rain", "Sun", "Snow"])]
    )

    for a in [
        ["Rain"],
        ["Sun"],
        ["Snow"],
    ]:
        factories.AnswerFactory(
            multiple_choice_answers=[("What do you like?", a)],
            question=question,
            consultation_response=factories.ConsultationResponseFactory(consultation=consultation),
        )

    result = question.multiple_choice_stats()
    stats = result[0]

    assert not stats.has_multiple_selections

    percentages = stats.percentages()

    assert percentages["Rain"] == 33
    assert percentages["Snow"] == 33
    assert percentages["Sun"] == 33
