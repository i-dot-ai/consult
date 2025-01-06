import pytest

from consultation_analyser.factories import ConsultationFactory, QuestionFactory


@pytest.mark.django_db
def test_consultation_save():
    consultation_title = "My First Consultation"
    slugified = "my-first-consultation"
    consultation = ConsultationFactory(text=consultation_title)
    assert consultation.slug == slugified
    another_consultation = ConsultationFactory(text=consultation_title)
    assert another_consultation.slug != consultation.slug
    assert another_consultation.slug.startswith(slugified)


@pytest.mark.django_db
def test_question_save():
    question_text = "What are your thoughts on the proposed changes?"
    slugified = "what-are-your-thoughts-on-the-proposed-changes"
    question = QuestionFactory(text=question_text)
    assert question.slug == slugified
    another_question = QuestionFactory(text=question_text)
    assert another_question.slug != question.slug
    assert another_question.slug.startswith(slugified)

    # Test empty quesiton text. This might occur if we have two related
    # question parts with no overarching question.
    question_text = ""
    question = QuestionFactory(text=question_text)
    assert question.slug
