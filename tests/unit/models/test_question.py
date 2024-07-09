import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import MultipleChoiceNotProportionalError


@pytest.mark.django_db
def test_get_multiple_choice_stats():
    consultation_builder = factories.ConsultationBuilder()
    question = consultation_builder.add_question(
        multiple_choice_questions=[("What do you like?", ["Rain", "Sun", "Snow"])]
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
        consultation_builder.add_answer(
            question, multiple_choice_answers=[("What do you like?", a)]
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
    consultation_builder = factories.ConsultationBuilder()
    question = consultation_builder.add_question(
        multiple_choice_questions=[("What do you like?", ["Rain", "Sun", "Snow"])]
    )

    for a in [
        ["Rain"],
        ["Sun"],
        ["Snow"],
    ]:
        consultation_builder.add_answer(
            question, multiple_choice_answers=[("What do you like?", a)]
        )

    result = question.multiple_choice_stats()
    stats = result[0]

    assert not stats.has_multiple_selections

    percentages = stats.percentages()

    assert percentages["Rain"] == 33
    assert percentages["Snow"] == 33
    assert percentages["Sun"] == 33
