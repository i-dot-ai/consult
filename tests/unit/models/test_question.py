import django
import pytest

from consultation_analyser.consultations.models import Question
from consultation_analyser.factories import (
    ConsultationFactory,
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
def test_question_unique_slugs():
    question_text = "What are your thoughts on the proposed changes?"
    slugified = "what-are-your-thoughts-on-the-proposed-changes"
    question = QuestionFactory(text=question_text, number=1)
    assert question.slug == f"{slugified}-1"  # New model appends number
    another_question = QuestionFactory(
        text=question_text, number=2, consultation=question.consultation
    )
    assert another_question.slug != question.slug
    assert another_question.slug == f"{slugified}-2"

    # Test empty question text. 
    question_text = ""
    question = QuestionFactory(text=question_text, number=3)
    assert question.slug == "3"  # Falls back to number when text is empty


@pytest.mark.django_db
def test_question_save_same_slug():
    question_text = "What are your thoughts on the proposed changes?"
    slugified = "what-are-your-thoughts-on-the-proposed-changes"
    consultation1 = ConsultationFactory()
    consultation2 = ConsultationFactory()
    question1 = QuestionFactory(text=question_text, number=1, consultation=consultation1)
    question2 = QuestionFactory(text=question_text, number=1, consultation=consultation2)
    # Can have the same slugs for questions for different consultations
    assert question1.slug == f"{slugified}-1"
    assert question2.slug == f"{slugified}-1"


@pytest.mark.django_db
def test_question_configuration():
    # Test free text only question (default)
    question = QuestionFactory()
    assert question.has_free_text
    assert not question.has_multiple_choice
    assert question.multiple_choice_options is None
    
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


@pytest.mark.django_db  
def test_question_save_too_long():
    long_title = "T" * 257
    question = QuestionFactory(text=long_title, number=1)
    # New model truncates at 240 chars and appends number
    assert len(question.slug) <= 256
    assert question.slug.endswith("-1")


@pytest.mark.django_db
def test_question_save_long_title_twice():
    title = "T" * 256
    question = QuestionFactory(text=title, number=1)
    # Slug is truncated to 240 chars plus "-1"
    assert question.slug == f"{'t' * 240}-1"
    question2 = QuestionFactory(text=title, number=3, consultation=question.consultation)
    assert question2.slug == f"{'t' * 240}-3"