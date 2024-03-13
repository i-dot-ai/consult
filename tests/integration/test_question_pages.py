import pytest
from tests.factories import QuestionFactory
from tests import factories


@pytest.mark.django_db
def test_get_question_page(client):
    question = QuestionFactory(text="How should funding be allocated?", slug="how-should-funding-be-allocated")

    response = client.get(f"/questions/{question.slug}")
    assert "How should funding be allocated?" in str(response.content)


def generate_question_with_themes():
    consultation = factories.ConsultationFactory(slug="c-slug")
    consultation_response = factories.ConsultationResponseFactory()
    section = factories.SectionFactory(consultation=consultation, slug="s-slug")
    question = factories.QuestionFactory(
        section=section,
        slug="question-slug",
        text="Is this an interesting question?",
        multiple_choice_options=[],
        has_free_text=False,
    )
    theme_1 = factories.ThemeFactory(summary="Summary theme 1", keywords=["summary", "one"])
    theme_2 = factories.ThemeFactory(summary="Summary theme 2", keywords=["summary", "two"])
    factories.AnswerFactory(question=question, theme=theme_1, consultation_response=consultation_response)
    factories.AnswerFactory(question=question, theme=theme_2, consultation_response=consultation_response)


@pytest.mark.django_db
def test_get_question_summary_page(client):
    generate_question_with_themes()
    question_summary_url = "/consultation/c-slug/section/s-slug/question-summary/question-slug/"
    response = client.get(question_summary_url)
    page_content = str(response.content)
    assert "Is this an interesting question?" in page_content
    assert "Summary theme 1" in page_content
    assert "Summary theme 2" in page_content
