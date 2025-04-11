import django
import pytest

from consultation_analyser.consultations.models import Question
from consultation_analyser.factories import ConsultationFactory, QuestionFactory


@pytest.mark.django_db
def test_unique_question_number():
    question_1 = QuestionFactory(number=1, text="question text")
    consultation = question_1.consultation
    question_2 = QuestionFactory(consultation=consultation, number=2)
    assert question_1.number != question_2.number
    with pytest.raises(django.db.utils.IntegrityError):
        Question.objects.get_or_create(consultation=consultation, number=1, text="different text")


@pytest.mark.django_db
def test_question_unique_slugs():
    question_text = "What are your thoughts on the proposed changes?"
    slugified = "what-are-your-thoughts-on-the-proposed-changes"
    question = QuestionFactory(text=question_text, number=1)
    assert question.slug == slugified
    another_question = QuestionFactory(
        text=question_text, number=2, consultation=question.consultation
    )
    assert another_question.slug != question.slug
    assert another_question.slug == f"{slugified}-2"

    # Test empty quesiton text. This might occur if we have two related
    # question parts with no overarching question.
    question_text = ""
    question = QuestionFactory(text=question_text)
    assert question.slug


@pytest.mark.django_db
def test_question_save_same_slug():
    question_text = "What are your thoughts on the proposed changes?"
    slugified = "what-are-your-thoughts-on-the-proposed-changes"
    consultation1 = ConsultationFactory()
    consultation2 = ConsultationFactory()
    question1 = QuestionFactory(text=question_text, number=1, consultation=consultation1)
    question2 = QuestionFactory(text=question_text, number=1, consultation=consultation2)
    # Can have the same slugs for questions for different consultations
    assert question1.slug == slugified
    assert question2.slug == slugified


@pytest.mark.django_db
def test_question_save_too_long():
    long_title = "T" * 257
    question = QuestionFactory(text=long_title)
    assert len(question.slug) == 256


@pytest.mark.django_db
def test_question_save_long_title_twice():
    title = "T" * 256
    question = QuestionFactory(text=title)
    assert question.slug == "t" * 256
    question2 = QuestionFactory(text=title, number=3, consultation=question.consultation)
    assert question2.slug == f"{'t' * 254}-{3}"
