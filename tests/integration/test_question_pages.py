import html
import re

import pytest

from consultation_analyser.factories import (
    AnswerFactory,
    ConsultationFactory,
    ConsultationResponseFactory,
    QuestionFactory,
    SectionFactory,
    UserFactory,
    ProcessingRunFactory,
    TopicModelMetadataFactory,
    ThemeFactory
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_get_question_summary_page(django_app):
    user = UserFactory()
    consultation = ConsultationFactory(user=user)
    section = SectionFactory(consultation=consultation)
    question = QuestionFactory(
        section=section, multiple_choice_questions=[("What do you think?", ["Yes", "No", "Maybe"])]
    )
    consultation_response = ConsultationResponseFactory(consultation=consultation)
    processing_run1 = ProcessingRunFactory(consultation=consultation)
    processing_run2= ProcessingRunFactory(consultation=consultation)
    topic_model_meta1 = TopicModelMetadataFactory(processing_run=processing_run1, question=question)
    topic_model_meta2 = TopicModelMetadataFactory(processing_run=processing_run2, question=question)
    theme1 = ThemeFactory(topic_model_metadata=topic_model_meta1)
    theme2 = ThemeFactory(topic_model_metadata=topic_model_meta2)
    ans = AnswerFactory(
        multiple_choice_answers=[("What do you think?", ["Yes"])],
        question=question,
        consultation_response=consultation_response,
    )
    ans.theme.add(theme1)
    ans.theme.add(theme2)
    ans = AnswerFactory(
        multiple_choice_answers=[("What do you think?", ["Yes"])],
        question=question,
        consultation_response=consultation_response,
    )
    ans.theme.add(theme1)
    ans.theme.add(theme2)
    ans = AnswerFactory(
        multiple_choice_answers=[("What do you think?", ["No"])],
        question=question,
        consultation_response=consultation_response,
    )
    ans.theme.add(theme1)
    ans.theme.add(theme2)
    ans = AnswerFactory(
        multiple_choice_answers=[("What do you think?", ["Maybe"])],
        question=question,
        consultation_response=consultation_response,
    )
    ans.theme.add(theme1)
    ans.theme.add(theme2)

    sign_in(django_app, user.email)

    question_summary_url = f"/consultations/{consultation.slug}/sections/{question.section.slug}/questions/{question.slug}/"

    question_page = django_app.get(question_summary_url)
    page_content = html.unescape(str(question_page.content))

    assert question.text in page_content

    answer = question.answer_set.first()
    assert answer.latest_theme.short_description in page_content

    for item in question.multiple_choice_options:
        for opt in item["options"]:
            assert opt in page_content

    for keyword in answer.latest_theme.topic_keywords:
        assert keyword in page_content

    assert re.search(r"Yes\s+50%", question_page.html.text)
    assert re.search(r"No\s+25%", question_page.html.text)
    assert re.search(r"Maybe\s+25%", question_page.html.text)
