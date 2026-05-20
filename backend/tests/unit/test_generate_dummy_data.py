import os
from unittest.mock import patch

import pytest

from consultations import models
from consultations.dummy_data import DUMMY_CONSULTATIONS, create_dummy_consultation


@pytest.mark.django_db
@patch("hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_a_consultation_is_generated(settings):
    assert models.Consultation.objects.count() == 0
    create_dummy_consultation()
    assert models.Consultation.objects.count() == 1
    assert models.Question.objects.count() == 4


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod"])
def test_the_tool_will_only_run_in_dev(environment):
    with patch.dict(os.environ, {"ENVIRONMENT": environment}):
        with pytest.raises(
            Exception, match=r"Dummy data generation should not be run in production"
        ):
            create_dummy_consultation()


@pytest.mark.django_db
def test_setup_stage_has_consultation_data_but_no_themes():
    config = DUMMY_CONSULTATIONS[0]
    consultation = create_dummy_consultation(number_respondents=10, config=config)
    questions = models.Question.objects.filter(consultation=consultation)

    assert consultation.stage == models.Consultation.Stage.SETUP
    assert questions.count() == 4
    assert models.Response.objects.filter(question__consultation=consultation).count() > 0
    assert models.CandidateTheme.objects.filter(question__consultation=consultation).count() == 0
    assert models.SelectedTheme.objects.filter(question__consultation=consultation).count() == 0

    # Multiple choice questions have answers
    q1 = questions.get(number=1)
    assert q1.has_multiple_choice
    assert models.MultiChoiceAnswer.objects.filter(question=q1).count() == 4

    # Respondents have demographic data
    respondent = models.Respondent.objects.filter(consultation=consultation).first()
    assert respondent.demographics.count() > 0
    field_names = set(respondent.demographics.values_list("field_name", flat=True))
    assert "region" in field_names
    assert "age_group" in field_names
    assert "respondent_type" in field_names


@pytest.mark.django_db
def test_theme_sign_off_draft_has_candidate_themes_and_responses():
    config = DUMMY_CONSULTATIONS[1]
    consultation = create_dummy_consultation(number_respondents=10, config=config)
    q4 = models.Question.objects.get(consultation=consultation, number=4)

    assert consultation.stage == models.Consultation.Stage.THEME_SIGN_OFF
    assert q4.theme_status == models.Question.ThemeStatus.DRAFT

    # Has candidate themes at multiple levels
    all_themes = models.CandidateTheme.objects.filter(question=q4)
    top_level = all_themes.filter(parent=None)
    children = all_themes.exclude(parent=None)
    assert top_level.count() > 0
    assert children.count() > 0

    # Has CandidateThemeResponses for child themes too
    child_theme = children.first()
    assert models.CandidateThemeResponse.objects.filter(candidate_theme=child_theme).exists()

    # No SelectedThemes (still draft)
    assert models.SelectedTheme.objects.filter(question=q4).count() == 0


@pytest.mark.django_db
def test_theme_sign_off_confirmed_has_selected_themes():
    config = DUMMY_CONSULTATIONS[2]
    consultation = create_dummy_consultation(number_respondents=10, config=config)
    q4 = models.Question.objects.get(consultation=consultation, number=4)

    assert consultation.stage == models.Consultation.Stage.THEME_SIGN_OFF
    assert q4.theme_status == models.Question.ThemeStatus.CONFIRMED

    # Has SelectedThemes
    selected_themes = models.SelectedTheme.objects.filter(question=q4)
    assert selected_themes.filter(key="A").exists()
    assert not selected_themes.filter(name="Other").exists()
    assert not selected_themes.filter(name="No Reason Given").exists()


@pytest.mark.django_db
def test_analysis_has_response_annotations():
    config = DUMMY_CONSULTATIONS[3]
    consultation = create_dummy_consultation(number_respondents=10, config=config)
    q1 = models.Question.objects.get(consultation=consultation, number=1)

    assert consultation.stage == models.Consultation.Stage.ANALYSIS
    assert q1.theme_status == models.Question.ThemeStatus.CONFIRMED

    # Has SelectedThemes including defaults
    selected_themes = models.SelectedTheme.objects.filter(question=q1)
    assert selected_themes.count() == 4
    assert selected_themes.get(key="A").name == "Standardized framework"
    assert selected_themes.filter(name="Other").exists()
    assert selected_themes.filter(name="No Reason Given").exists()

    # Has ResponseAnnotations for responses
    annotations = models.ResponseAnnotation.objects.filter(response__question=q1)
    assert annotations.count() > 0

    # Each annotation has themes assigned
    for annotation in annotations:
        assert annotation.themes.count() > 0
