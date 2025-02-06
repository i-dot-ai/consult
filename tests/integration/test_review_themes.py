import pytest
from django.urls import reverse

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    ExecutionRunFactory,
    FreeTextAnswerFactory,
    InitialFrameworkFactory,
    InitialThemeFactory,
    ThemeMappingFactory,
    UserFactory,
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_review_show_response(django_app):
    user = UserFactory()
    framework = InitialFrameworkFactory()
    question_part = framework.question_part
    consultation = question_part.question.consultation
    consultation_slug = consultation.slug
    question_slug = question_part.question.slug

    consultation.users.add(user)
    theme_a = InitialThemeFactory(framework=framework, name="Theme A")
    theme_b = InitialThemeFactory(framework=framework, name="Theme B")
    answer_1 = FreeTextAnswerFactory(question_part=question_part)
    answer_2 = FreeTextAnswerFactory(question_part=question_part)
    execution_run = ExecutionRunFactory(framework=framework)
    ThemeMappingFactory(answer=answer_1, theme=theme_a, execution_run=execution_run)
    ThemeMappingFactory(answer=answer_2, theme=theme_a, execution_run=execution_run)
    ThemeMappingFactory(answer=answer_2, theme=theme_b, execution_run=execution_run)

    sign_in(django_app, user.email)

    # Test adding a theme on review
    response_id = answer_1.id
    url = reverse(
        "show_response",
        args=(
            consultation_slug,
            question_slug,
            response_id,
        ),
    )
    review_response_page = django_app.get(url)
    review_response_page.form["theme"] = [str(theme_b.id)]
    next_response = review_response_page.form.submit().follow()
    assert "No responses" not in next_response  # Haven't reviewed all responses

    # Check that the answer is now audited, and themes are updated
    updated_answer = models.Answer.objects.get(id=response_id)
    assert updated_answer.is_theme_mapping_audited
    theme_mapping = models.ThemeMapping.objects.get(answer=updated_answer)
    assert theme_mapping.theme == theme_b

    # And check user who made the change has been saved
    latest_answer_history = updated_answer.history.latest()
    assert latest_answer_history.history_user == user

    # Now test reviewing a response - making no further changes
    response_id = answer_2.id
    url = reverse(
        "show_response",
        args=(
            consultation_slug,
            question_slug,
            response_id,
        ),
    )
    review_response_page = django_app.get(url)
    # Same themes
    review_response_page.form["theme"] = [str(theme_a.id), str(theme_b.id)]
    next_response = review_response_page.form.submit().follow()
    assert "No responses" in next_response  # We have reviewed all responses

    # Check that the answer is now audited, and the theme mappings are unchanged
    updated_answer = models.Answer.objects.get(id=response_id)
    assert updated_answer.is_theme_mapping_audited
    assert models.ThemeMapping.objects.filter(answer=updated_answer).count() == 2

    # Check the latest user who made the change has been saved
    latest_answer_history = updated_answer.history.latest()
    assert latest_answer_history.history_user == user
