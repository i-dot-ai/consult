import django
import pytest

from consultation_analyser.consultations.models import Question
from consultation_analyser.factories import (
    QuestionFactory,
    QuestionWithBothFactory,
    QuestionWithMultipleChoiceFactory,
)


@pytest.mark.django_db
def test_unique_question_number():
    question_1 = QuestionFactory(number=1, text="question text")
    consultation = question_1.consultation
    question_2 = QuestionFactory(consultation=consultation, number=2)
    assert question_1.number != question_2.number
    with pytest.raises(django.db.utils.IntegrityError):
        Question.objects.get_or_create(consultation=consultation, number=1, text="different text")


@pytest.mark.django_db
def test_question_configuration(free_text_question):
    # Test free text only question (default)
    assert free_text_question.has_free_text
    assert not free_text_question.has_multiple_choice
    assert free_text_question.multiple_choice_options == []

    # Test multiple choice only question
    mc_question = QuestionWithMultipleChoiceFactory()
    assert mc_question.has_multiple_choice
    assert not mc_question.has_free_text  # Factory sets this to False
    assert isinstance(mc_question.multiple_choice_options, list)
    assert len(mc_question.multiple_choice_options) >= 2

    # Test question with both
    both_question = QuestionWithBothFactory()
    assert both_question.has_free_text
    assert both_question.has_multiple_choice
    assert isinstance(both_question.multiple_choice_options, list)
