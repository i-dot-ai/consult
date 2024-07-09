import html
import re

import pytest

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    ConsultationWithThemesFactory,
    UserFactory,
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    user = UserFactory()
    consultation = ConsultationWithThemesFactory(users=(user))

    question = models.Question.objects.filter(section__consultation=consultation).first()
    processing_run = consultation.latest_processing_run

    sign_in(django_app, user.email)

    question_summary_url = f"/consultations/{consultation.slug}/sections/{question.section.slug}/questions/{question.slug}/"

    question_page = django_app.get(question_summary_url)
    page_content = html.unescape(str(question_page.content))

    assert question.text in page_content

    latest_theme = (
        processing_run.get_themes_for_question(question_id=question.id)
        .filter(is_outlier=False)
        .last()
    )
    assert latest_theme.short_description in page_content

    for item in question.multiple_choice_options:
        for opt in item["options"]:
            assert opt in page_content

    for keyword in latest_theme.topic_keywords:
        assert keyword in page_content

    assert re.search(r"Yes\s+\d\s+\d+%", question_page.html.text)
    assert re.search(r"No\s+\d\s+\d+%", question_page.html.text)
