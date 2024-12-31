import pytest

from consultation_analyser.factories2 import Consultation2Factory, Question2Factory


@pytest.mark.django_db
def test_consultation_save():
    consultation_title = "My First Consultation"
    slugified = "my-first-consultation"
    consultation = Consultation2Factory(text=consultation_title)
    assert consultation.slug.startswith(slugified)
    another_consultation = Consultation2Factory(text=consultation_title)
    assert another_consultation.slug != consultation.slug
    assert another_consultation.slug.startswith(slugified)


@pytest.mark.django_db
def test_question_save():
    question_text = "What are your thoughts on the proposed changes?"
    slugified = "what-are-your-thoughts-on-the-proposed-changes"
    question = Question2Factory(text=question_text)
    assert question.slug.startswith(slugified)
    another_question = Question2Factory(text=question_text)
    assert another_question.slug != question.slug
    assert another_question.slug.startswith(slugified)




