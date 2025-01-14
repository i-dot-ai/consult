import django
import pytest

from consultation_analyser.consultations.models import QuestionPart
from consultation_analyser.factories import (
    FreeTextQuestionPartFactory,
    QuestionFactory,
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
