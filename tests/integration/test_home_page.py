import pytest


from tests.factories import ConsultationFactory


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    consultation = ConsultationFactory(with_question=True)
    question = consultation.section_set.first().question_set.first()
    homepage = django_app.get("/")
    question_page = homepage.click(f"{question.text}")

    assert "Question summary" in question_page
    assert f"{question.text}" in question_page
