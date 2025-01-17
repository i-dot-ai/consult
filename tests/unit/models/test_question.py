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


@pytest.mark.django_db
def test_question_save():
    question_text = "What are your thoughts on the proposed changes?"
    slugified = "what-are-your-thoughts-on-the-proposed-changes"
    question = QuestionFactory(text=question_text, number=1)
    assert question.slug == slugified
    another_question = QuestionFactory(text=question_text, number=2)
    assert another_question.slug != question.slug
    assert another_question.slug == f"{slugified}-2"

    # Test empty quesiton text. This might occur if we have two related
    # question parts with no overarching question.
    question_text = ""
    question = QuestionFactory(text=question_text)
    assert question.slug
