import html

import pytest
from waffle.testutils import override_switch

from consultation_analyser.factories import ConsultationFactory, UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
@override_switch("FRONTEND_USER_LOGIN", True)
def test_get_question_responses_page(django_app):
    user = UserFactory(email="email@example.com")
    sign_in(django_app, "email@example.com")

    consultation = ConsultationFactory(
        user=user,
        with_question=True,
        with_question__with_answer=True,
        with_question__with_multiple_choice=True,
        with_question__with_free_text=True,
    )
    section = consultation.section_set.first()
    question = section.question_set.first()
    answers = question.answer_set.all()
    question_responses_url = f"/consultations/{consultation.slug}/sections/{section.slug}/responses/{question.slug}/"
    responses_page = django_app.get(question_responses_url)
    page_content = html.unescape(str(responses_page.content))

    assert "Responses" in page_content
    assert f"{question.text}" in page_content

    # Check responses appear
    answer_loop_range = min(4, len(answers))
    for i in range(answer_loop_range):
        assert f"{answers[i].free_text}" in page_content
        assert f"{answers[i].multiple_choice[0]}" in page_content
        if answers[i].free_text:
            assert f"{answers[i].theme.short_description}" in page_content

    # Opinions should appear in filter select-box
    for item in question.multiple_choice_options:
        for opt in item["options"]:
            assert opt in page_content

    # Check keyword filtering
    first_word_of_answer = answers[0].free_text.split()[0]
    keywords = ["ThisWordWontAppear", first_word_of_answer]
    for keyword in keywords:
        responses_page = django_app.get(f"{question_responses_url}?keyword={keyword}")
        page_content = html.unescape(str(responses_page.content))
        assert keyword in page_content
        if keyword == "ThisWordWontAppear":
            assert f"Showing <strong>0</strong> of <strong>{len(answers)}</strong> reponses"
