import os
from unittest.mock import patch

import pytest

from consultations import models
from consultations.dummy_data import DUMMY_CONSULTATIONS, create_dummy_consultation
from factories import UserFactory


@pytest.mark.django_db
@patch("hosting_environment.HostingEnvironment.is_local", return_value=True)
def test_a_consultation_is_generated(settings):
    assert models.Consultation.objects.count() == 0
    create_dummy_consultation()
    assert models.Consultation.objects.count() == 1
    assert models.Question.objects.count() == 7


@pytest.mark.django_db
def test_generated_consultation_is_assigned_to_staff_users_only():
    staff_user = UserFactory(is_staff=True)
    non_staff_user = UserFactory(is_staff=False)

    consultation = create_dummy_consultation()

    assert staff_user in consultation.users.all()
    assert non_staff_user not in consultation.users.all()


@pytest.mark.django_db
@pytest.mark.parametrize("environment", ["prod"])
def test_the_tool_will_only_run_in_dev(environment):
    with (
        patch.dict(os.environ, {"ENVIRONMENT": environment}),
        pytest.raises(Exception, match=r"Dummy data generation should not be run in production"),
    ):
        create_dummy_consultation()


@pytest.mark.django_db
def test_setup_stage_is_at_the_start_of_the_import_flow():
    config = DUMMY_CONSULTATIONS[0]
    consultation = create_dummy_consultation(number_respondents=10, config=config)
    assert consultation.stage == models.Consultation.Stage.SETUP
    assert consultation.survey_import_status == models.Consultation.SurveyImportStatus.NOT_STARTED
    assert not models.Question.objects.filter(consultation=consultation).exists()
    assert not models.Respondent.objects.filter(consultation=consultation).exists()
    assert not models.Response.objects.filter(question__consultation=consultation).exists()
    assert models.CandidateTheme.objects.filter(question__consultation=consultation).count() == 0
    assert models.SelectedTheme.objects.filter(question__consultation=consultation).count() == 0


@pytest.mark.django_db
def test_generated_data_uses_v2_schema():
    consultation = create_dummy_consultation(
        number_respondents=10, config=DUMMY_CONSULTATIONS[1]
    )
    questions = models.Question.objects.filter(consultation=consultation)

    assert consultation.data_source == models.Consultation.DataSource.CITIZEN_SPACE
    assert consultation.survey_import_status == models.Consultation.SurveyImportStatus.IMPORT_COMPLETE
    assert questions.filter(type=models.Question.QuestionType.OPEN).count() == 2
    assert questions.filter(type=models.Question.QuestionType.CLOSED).count() == 2
    assert questions.filter(type=models.Question.QuestionType.DEMOGRAPHIC).count() == 3
    assert not questions.filter(type__isnull=True).exists()

    closed_question = questions.get(number=1)
    open_question = questions.get(number=2)
    assert open_question.closed_question == closed_question

    open_responses = models.Response.objects.filter(question=open_question)
    assert open_responses.count() == 10
    assert not open_responses.filter(text__isnull=True).exists()
    assert not open_responses.filter(free_text__isnull=True).exists()

    packaging_question = questions.get(number=3)
    assert models.Response.objects.filter(question=packaging_question).count() > 10
    assert not models.Response.objects.filter(question=packaging_question).exclude(
        free_text__isnull=True
    ).exists()

    demographic_questions = questions.filter(type=models.Question.QuestionType.DEMOGRAPHIC)
    assert models.Response.objects.filter(question__in=demographic_questions).count() == 30
    assert not models.MultiChoiceAnswer.objects.filter(question__consultation=consultation).exists()
    assert not models.DemographicOption.objects.filter(consultation=consultation).exists()


@pytest.mark.django_db
def test_theme_sign_off_draft_has_candidate_themes_and_responses():
    config = DUMMY_CONSULTATIONS[1]
    consultation = create_dummy_consultation(number_respondents=10, config=config)
    q4 = models.Question.objects.get(consultation=consultation, number=4)

    assert consultation.stage == models.Consultation.Stage.FINALISING_THEMES
    assert q4.status == models.Question.ThemeStatus.FINALISING_THEMES
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

    assert consultation.stage == models.Consultation.Stage.ASSIGNING_THEMES
    assert q4.status == models.Question.ThemeStatus.CONFIRMED
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
    q1 = models.Question.objects.get(consultation=consultation, number=2)

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
