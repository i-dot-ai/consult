import django
import pytest

from consultation_analyser.consultations.models import QuestionPart
from consultation_analyser.factories import (
    FreeTextQuestionPartFactory,
    QuestionFactory,
    SingleOptionQuestionPartFactory,
    FreeTextAnswerFactory,
    SingleOptionAnswerFactory,
    MultipleOptionQuestionPartFactory,
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
