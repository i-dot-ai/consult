"""
Test factories for the new consultation models.
"""

import pytest

from consultation_analyser import factories
from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models
from consultation_analyser.consultations.models import MultiChoiceAnswer


@pytest.mark.django_db
def test_user_factory():
    user = factories.UserFactory()
    assert User.objects.filter(id=user.id).exists()
    assert user.email
    assert not user.is_staff


@pytest.mark.django_db
def test_consultation_factory():
    consultation = factories.ConsultationFactory()
    assert models.Consultation.objects.filter(id=consultation.id).exists()
    assert consultation.title
    assert consultation.slug


@pytest.mark.django_db
def test_question_factories():
    # Test basic question with free text
    question = factories.QuestionFactory()
    assert models.Question.objects.filter(id=question.id).exists()
    assert question.has_free_text
    assert not question.has_multiple_choice
    assert not MultiChoiceAnswer.objects.filter(question=question).exists()

    # Test question with multiple choice only
    mc_question = factories.QuestionWithMultipleChoiceFactory()
    assert mc_question.has_multiple_choice
    assert mc_question.multiple_choice_options
    assert len(mc_question.multiple_choice_options) >= 2

    # Test question with both free text and multiple choice
    both_question = factories.QuestionWithBothFactory()
    assert both_question.has_free_text
    assert both_question.has_multiple_choice
    assert both_question.multiple_choice_options


@pytest.mark.django_db
def test_respondent_factory():
    respondent = factories.RespondentFactory()
    assert models.Respondent.objects.filter(id=respondent.id).exists()
    assert respondent.themefinder_id
    assert respondent.demographics


@pytest.mark.django_db
def test_response_factories():
    # Test basic response with free text
    response = factories.ResponseFactory()
    assert models.Response.objects.filter(id=response.id).exists()
    assert response.free_text
    assert response.chosen_options.count() == 0

    # Test response with multiple choice
    mc_response = factories.ResponseWithMultipleChoiceFactory()
    assert mc_response.free_text == ""
    assert mc_response.chosen_options
    assert all(
        opt in mc_response.question.multiple_choice_options
        for opt in mc_response.chosen_options.all()
    )

    # Test response with both
    both_response = factories.ResponseWithBothFactory()
    assert both_response.free_text
    assert both_response.chosen_options


@pytest.mark.django_db
def test_theme_factory():
    theme = factories.ThemeFactory()
    assert models.Theme.objects.filter(id=theme.id).exists()
    assert theme.name
    assert theme.description
    assert theme.key


@pytest.mark.django_db
def test_response_annotation_factory():
    annotation = factories.ResponseAnnotationFactory()
    assert models.ResponseAnnotation.objects.filter(id=annotation.id).exists()
    assert annotation.sentiment in [choice.value for choice in models.ResponseAnnotation.Sentiment]
    assert isinstance(annotation.evidence_rich, bool)
    assert not annotation.human_reviewed
    assert annotation.themes.count() >= 1

    # Test themes are for the same question
    for theme in annotation.themes.all():
        assert theme.question == annotation.response.question


@pytest.mark.django_db
def test_reviewed_response_annotation_factory():
    reviewed = factories.ReviewedResponseAnnotationFactory()
    assert reviewed.human_reviewed
    assert reviewed.reviewed_by
    assert reviewed.reviewed_at
