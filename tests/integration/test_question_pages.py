import pytest


from tests.factories import ConsultationFactory


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    consultation = ConsultationFactory(with_question=True, with_question__with_answer=True)
    section = consultation.section_set.first()
    question = section.question_set.first()
    answer = question.answer_set.first()
    question_summary_url = f"/consultations/{consultation.slug}/sections/{section.slug}/questions/{question.slug}"

    question_page = django_app.get(question_summary_url)

    assert question.text in question_page
    assert answer.theme.summary in question_page
