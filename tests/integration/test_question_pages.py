import pytest


from tests.factories import AnswerFactory


@pytest.mark.django_db
def test_get_question_summary_page(client):
    answer = AnswerFactory()
    question = answer.question
    section = question.section
    consultation = section.consultation
    question_summary_url = f"/consultations/{consultation.slug}/sections/{section.slug}/questions/{question.slug}"
    response = client.get(question_summary_url)
    page_content = str(response.content)
    assert question.text in page_content
    assert answer.theme.summary in page_content
