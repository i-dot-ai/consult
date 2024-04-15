import html
import re

import pytest

from consultation_analyser.factories import AnswerFactory, ConsultationFactory


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    consultation = ConsultationFactory(with_question=True, with_question__with_free_text=True)
    section = consultation.section_set.first()
    question = section.question_set.first()

    AnswerFactory(multiple_choice_responses=["Yes"], question=question)
    AnswerFactory(multiple_choice_responses=["Yes"], question=question)
    AnswerFactory(multiple_choice_responses=["No"], question=question)
    AnswerFactory(multiple_choice_responses=["Maybe"], question=question)

    question_summary_url = f"/consultations/{consultation.slug}/sections/{section.slug}/questions/{question.slug}"
    question_page = django_app.get(question_summary_url)
    page_content = html.unescape(str(question_page.content))

    assert question.text in page_content

    answer = question.answer_set.first()
    assert answer.theme.summary in page_content

    for keyword in answer.theme.keywords:
        assert keyword in page_content

    assert re.search(r"Yes\s+50%", question_page.html.text)
    assert re.search(r"No\s+25%", question_page.html.text)
    assert re.search(r"Maybe\s+25%", question_page.html.text)
