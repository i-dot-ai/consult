import html
import re

import pytest
from waffle.testutils import override_switch

from consultation_analyser.factories import AnswerFactory, ConsultationFactory, UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
@override_switch("FRONTEND_USER_LOGIN", True)
def test_get_question_summary_page(django_app):
    user = UserFactory()
    consultation = ConsultationFactory(with_question=True, with_question__with_free_text=True, user=user)

    sign_in(django_app, user.email)

    section = consultation.section_set.first()
    question = section.question_set.first()

    AnswerFactory(multiple_choice=["Yes"], question=question)
    AnswerFactory(multiple_choice=["Yes"], question=question)
    AnswerFactory(multiple_choice=["No"], question=question)
    AnswerFactory(multiple_choice=["Maybe"], question=question)

    question_summary_url = f"/consultations/{consultation.slug}/sections/{section.slug}/questions/{question.slug}/"

    question_page = django_app.get(question_summary_url)
    page_content = html.unescape(str(question_page.content))

    assert question.text in page_content

    answer = question.answer_set.first()
    assert answer.theme.summary in page_content

    for option in question.multiple_choice_options:
        assert option in page_content

    for keyword in answer.theme.keywords:
        assert keyword in page_content

    assert re.search(r"Yes\s+50%", question_page.html.text)
    assert re.search(r"No\s+25%", question_page.html.text)
    assert re.search(r"Maybe\s+25%", question_page.html.text)

    filtered_page = django_app.get(f"{question_summary_url}?opinion=Yes")
    assert re.search(r"Yes\s+100%", filtered_page.html.text)
    assert re.search(r"No\s+0%", filtered_page.html.text)
    assert re.search(r"Maybe\s+0%", filtered_page.html.text)
