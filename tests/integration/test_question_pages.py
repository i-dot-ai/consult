import pytest
from tests.factories import QuestionFactory
from tests import factories


@pytest.mark.django_db
def test_get_question_summary_page(client):
    factories.AnswerFactory(specific_theme=True)
    question_summary_url = "/consultation/consultation-slug/section/section-slug/question/question-slug/"
    response = client.get(question_summary_url)
    page_content = str(response.content)
    assert "Is this an interesting question?" in page_content
    assert "Summary theme 1" in page_content
