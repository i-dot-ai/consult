import html
import re

import pytest

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    ConsultationBuilder,
    UserFactory,
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    user = UserFactory()
    consultation_builder = ConsultationBuilder(user=(user))
    consultation = consultation_builder.consultation
    question = consultation_builder.add_question(
        multiple_choice_questions=[("Do you agree?", ["Yes", "No", "Maybe"])]
    )
    theme = consultation_builder.add_theme(topic_id=1) # prevent outlier

    for a in [
        [("Do you agree?", ["Yes"])],
        [("Do you agree?", ["No"])],
        [("Do you agree?", ["No"])],
        [("Do you agree?", ["Maybe"])],
    ]:
        answer = consultation_builder.add_answer(question, multiple_choice_answers=a)
        answer.themes.add(theme)

    sign_in(django_app, user.email)

    question_summary_url = f"/consultations/{consultation.slug}/sections/{question.section.slug}/questions/{question.slug}/"

    question_page = django_app.get(question_summary_url)
    page_content = html.unescape(str(question_page.content))

    assert question.text in page_content

    assert theme.short_description in page_content

    for item in question.multiple_choice_options:
        for opt in item["options"]:
            assert opt in page_content

    for keyword in theme.topic_keywords:
        assert keyword in page_content

    assert re.search(r"Yes\s+1\s+25%", question_page.html.text)
    assert re.search(r"No\s+2\s+50%", question_page.html.text)
    assert re.search(r"Maybe\s+1\s+25%", question_page.html.text)
