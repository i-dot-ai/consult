import pytest
from tests.factories import QuestionFactory


@pytest.mark.django_db
def test_get_question_page(client):
    question = QuestionFactory(text="How should funding be allocated?", slug="how-should-funding-be-allocated")

    response = client.get(f"/questions/{question.slug}")
    assert "How should funding be allocated?" in str(response.content)
