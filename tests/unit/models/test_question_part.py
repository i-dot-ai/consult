from collections import OrderedDict

import django
import pytest

from consultation_analyser.consultations.models import QuestionPart
from consultation_analyser.factories import (
    FreeTextAnswerFactory,
    FreeTextQuestionPartFactory,
    MultipleOptionAnswerFactory,
    MultipleOptionQuestionPartFactory,
    QuestionFactory,
    SingleOptionAnswerFactory,
    SingleOptionQuestionPartFactory,
)


@pytest.mark.django_db
def test_only_one_free_text():
    question = QuestionFactory()
    # Have a question with no free text - shouldn't error
    SingleOptionQuestionPartFactory(question=question, number=1)

    # Shouldn't error if we add one free text part
    part = FreeTextQuestionPartFactory(question=question, number=2)
    assert part.type == QuestionPart.QuestionType.FREE_TEXT

    # Should error if we try to add another free text part
    with pytest.raises(django.db.utils.IntegrityError) as excinfo:
        FreeTextQuestionPartFactory(question=question, number=3)
        excinfo.match(
            "UNIQUE constraint failed: consultations_questionpart.question_id, consultations_questionpart.type"
        )


@pytest.mark.django_db
def test_proportion_of_auditted_answers_no_answers():
    question_part = FreeTextQuestionPartFactory()
    assert question_part.proportion_of_audited_answers == 0
    # Test with other question types to check it doesn't break
    # In practice, this makes no sense and won't be used
    question_part = SingleOptionQuestionPartFactory()
    assert question_part.proportion_of_audited_answers == 0
    question_part = MultipleOptionQuestionPartFactory()
    assert question_part.proportion_of_audited_answers == 0


@pytest.mark.django_db
def test_proportion_of_auditted_answers_some_audited():
    question_part = FreeTextQuestionPartFactory()
    for _ in range(3):
        FreeTextAnswerFactory(question_part=question_part, is_theme_mapping_audited=True)
    for _ in range(2):
        FreeTextAnswerFactory(question_part=question_part, is_theme_mapping_audited=False)
    assert question_part.proportion_of_audited_answers == 0.6


@pytest.mark.django_db
def test_get_option_counts():
    # Free text question parts don't have options
    free_text_question_part = FreeTextQuestionPartFactory()
    for _ in range(3):
        FreeTextAnswerFactory(question_part=free_text_question_part)
    assert free_text_question_part.get_option_counts() == {}

    # Single option questions have at most one option
    single_option_question_part = SingleOptionQuestionPartFactory(options=["blue", "red", "green"])
    SingleOptionAnswerFactory(question_part=single_option_question_part, chosen_options=["blue"])
    SingleOptionAnswerFactory(question_part=single_option_question_part, chosen_options=["red"])
    SingleOptionAnswerFactory(question_part=single_option_question_part, chosen_options=["blue"])
    SingleOptionAnswerFactory(question_part=single_option_question_part, chosen_options=[])
    expected = OrderedDict([("blue", 2), ("red", 1), ("green", 0)])
    actual = single_option_question_part.get_option_counts()
    assert expected == actual

    # Multiple option questions may have more than one chosen option
    multiple_option_question_part = MultipleOptionQuestionPartFactory(
        options=["blue", "red", "green"]
    )
    MultipleOptionAnswerFactory(
        question_part=multiple_option_question_part, chosen_options=["blue", "green"]
    )
    MultipleOptionAnswerFactory(
        question_part=multiple_option_question_part, chosen_options=["red", "green"]
    )
    MultipleOptionAnswerFactory(
        question_part=multiple_option_question_part, chosen_options=["blue"]
    )
    MultipleOptionAnswerFactory(question_part=multiple_option_question_part, chosen_options=[])
    expected = OrderedDict([("blue", 2), ("red", 1), ("green", 2)])
    actual = multiple_option_question_part.get_option_counts()
    assert expected == actual
