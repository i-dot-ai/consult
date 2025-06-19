import pytest
from django.urls import reverse

from consultation_analyser.consultations import models
from consultation_analyser.factories import (
    QuestionWithBothFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    ThemeFactory,
    UserFactory,
)
from tests.helpers import sign_in


@pytest.mark.django_db
def test_review_show_response(django_app):
    user = UserFactory()
    question = QuestionWithBothFactory()
    consultation = question.consultation
    consultation.users.add(user)
    respondent1 = RespondentFactory(consultation=consultation)
    respondent2 = RespondentFactory(consultation=consultation)
    response1 = ResponseFactory(respondent=respondent1, question=question)
    response2 = ResponseFactory(respondent=respondent2, question=question)

    # Add some themes
    theme_a = ThemeFactory(question=question, key="A")
    theme_b = ThemeFactory(question=question, key="B")
    response_annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
    response_annotation1.add_original_ai_themes([theme_a])
    response_annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
    response_annotation2.add_original_ai_themes([theme_a, theme_b])

    sign_in(django_app, user.email)

    # Review response 1 - test adding a theme on review
    url = reverse("show_response", args=(consultation.slug, question.slug, response1.id))
    review_response_page = django_app.get(url)
    review_response_page.form["theme"] = [str(theme_a.id), str(theme_b.id)]
    next_response = review_response_page.form.submit().follow()
    assert "No responses" not in next_response  # Haven't reviewed all responses

    # Check the response (annotation) is now audited
    response_annotation1.refresh_from_db()
    assert set(response_annotation1.themes.all()) == set([theme_a, theme_b])

    assert response_annotation1.human_reviewed
    assert response_annotation1.reviewed_by == user

    # Check that we have a record of what has been human reviewed in the theme annotation
    ai_annotation_themes = models.ResponseAnnotationTheme.objects.filter(
        response_annotation=response_annotation1, is_original_ai_assignment=True
    )
    assert set(ai_annotation_themes.values_list("theme_id", flat=True)) == set([theme_a.id])
    human_reviewed_themes = models.ResponseAnnotationTheme.objects.filter(
        response_annotation=response_annotation1, is_original_ai_assignment=False
    )
    assert set(human_reviewed_themes.values_list("theme_id", flat=True)) == set(
        [theme_a.id, theme_b.id]
    )

    # Now test reviewing a response making no further changes
    url = reverse("show_response", args=(consultation.slug, question.slug, response2.id))
    review_response_page = django_app.get(url)
    review_response_page.form["theme"] = [str(theme_a.id), str(theme_b.id)]
    next_response = review_response_page.form.submit().follow()

    # Check response annotation is now audited
    response_annotation2.refresh_from_db()
    assert response_annotation2.human_reviewed

    # Check the response themes are marked correctly.
    models.ResponseAnnotationTheme.objects.filter(
        response_annotation=response_annotation2, is_original_ai_assignment=True
    ).count() == 2
    models.ResponseAnnotationTheme.objects.filter(
        response_annotation=response_annotation2, is_original_ai_assignment=False
    ).count() == 2
