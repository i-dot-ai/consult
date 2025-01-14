import django
import pytest

from consultation_analyser.factories import QuestionFactory


@pytest.mark.django_db
def test_unique_question_number():
    question_1 = QuestionFactory(number=1)
    consultation = question_1.consultation
    question_2 = QuestionFactory(consultation=consultation, number=2)
    assert question_1.number != question_2.number
    with pytest.raises(django.db.utils.IntegrityError):
        QuestionFactory(consultation=consultation, number=1)



