from datetime import datetime, timezone

import pytest

DASHBOARD_ACCESS = "Dashboard access"


@pytest.mark.django_db()
def test_0004_dashboard_permission(migrator):
    # Check group doesn't exist before migration
    old_state = migrator.apply_initial_migration(
        ("authentication", "0003_user_groups_user_is_superuser_user_user_permissions")
    )
    Group = old_state.apps.get_model("auth", "Group")
    assert not Group.objects.filter(name=DASHBOARD_ACCESS).exists()

    # Run the migration that creates the group
    new_state = migrator.apply_tested_migration(("authentication", "0004_dashboard_permission"))

    # Verify that the group is created successfully
    Group = new_state.apps.get_model("auth", "Group")
    assert Group.objects.filter(name=DASHBOARD_ACCESS).exists()

    # Cleanup:
    migrator.reset()


@pytest.mark.django_db()
def test_0043_convert_jsonfield_data_to_json(migrator):
    old_state = migrator.apply_initial_migration(
        ("consultations", "0042_respondent_themefinder_respondent_id")
    )

    Consultation = old_state.apps.get_model("consultations", "Consultation")
    Question = old_state.apps.get_model("consultations", "Question")
    QuestionPart = old_state.apps.get_model("consultations", "QuestionPart")
    Respondent = old_state.apps.get_model("consultations", "Respondent")
    Answer = old_state.apps.get_model("consultations", "Answer")

    consultation = Consultation.objects.create(title="Consultation")
    question = Question.objects.create(consultation=consultation)
    qp = QuestionPart.objects.create(options='["option1", "option2"]', question=question)
    respondent = Respondent.objects.create(data='{"key": "value"}', consultation=consultation)
    answer_1 = Answer.objects.create(
        chosen_options='["option1", "option2"]', question_part=qp, respondent=respondent
    )
    answer_2 = Answer.objects.create(
        chosen_options="option1", question_part=qp, respondent=respondent
    )

    new_state = migrator.apply_tested_migration(
        ("consultations", "0043_convert_jsonfield_data_to_json")
    )

    QuestionPart = new_state.apps.get_model("consultations", "QuestionPart")
    Respondent = new_state.apps.get_model("consultations", "Respondent")
    Answer = new_state.apps.get_model("consultations", "Answer")

    qp = QuestionPart.objects.get(pk=qp.pk)
    respondent = Respondent.objects.get(pk=respondent.pk)
    answer_1 = Answer.objects.get(pk=answer_1.pk)
    answer_2 = Answer.objects.get(pk=answer_2.pk)

    assert qp.options == ["option1", "option2"]
    assert type(qp.options) is list
    assert respondent.data == {"key": "value"}
    assert type(respondent.data) is dict
    assert answer_1.chosen_options == ["option1", "option2"]
    assert type(answer_1.chosen_options) is list
    assert answer_2.chosen_options == ["option1"]
    assert type(answer_2.chosen_options) is list

    # Cleanup:
    migrator.reset()


@pytest.mark.django_db()
def test_0044_delete_duplicate_theme_mappings(migrator):
    old_state = migrator.apply_initial_migration(
        ("consultations", "0043_convert_jsonfield_data_to_json")
    )
    # Set-up old models
    Consultation = old_state.apps.get_model("consultations", "Consultation")
    Question = old_state.apps.get_model("consultations", "Question")
    QuestionPart = old_state.apps.get_model("consultations", "QuestionPart")
    Answer = old_state.apps.get_model("consultations", "Answer")
    Theme = old_state.apps.get_model("consultations", "Theme")
    ThemeMapping = old_state.apps.get_model("consultations", "ThemeMapping")
    Respondent = old_state.apps.get_model("consultations", "Respondent")
    Framework = old_state.apps.get_model("consultations", "Framework")
    ExecutionRun = old_state.apps.get_model("consultations", "ExecutionRun")

    # Set-up example consultation
    consultation = Consultation.objects.create(title="Consultation")
    respondent = Respondent.objects.create(consultation=consultation)
    execution_run = ExecutionRun.objects.create(type="theme_mapping")
    question = Question.objects.create(consultation=consultation)
    qp = QuestionPart.objects.create(type="free_text", question=question)
    framework = Framework.objects.create(execution_run=execution_run, question_part=qp)
    answer1 = Answer.objects.create(question_part=qp, respondent=respondent)
    answer2 = Answer.objects.create(question_part=qp, respondent=respondent)
    theme1 = Theme.objects.create(name="Theme 1", framework=framework)
    theme2 = Theme.objects.create(name="Theme 2", framework=framework)

    # Set-up theme mappings with some duplicates
    tm1 = ThemeMapping.objects.create(answer=answer1, theme=theme1)
    duplicate0 = ThemeMapping.objects.create(answer=answer1, theme=theme2)
    duplicate1 = ThemeMapping.objects.create(answer=answer1, theme=theme2)
    duplicate2 = ThemeMapping.objects.create(answer=answer1, theme=theme2)
    tm2 = ThemeMapping.objects.create(answer=answer2, theme=theme1)

    # Run migration
    new_state = migrator.apply_tested_migration(
        ("consultations", "0044_delete_duplicate_theme_mappings")
    )

    ThemeMapping = new_state.apps.get_model("consultations", "ThemeMapping")

    # Check that non-duplicates, and the first duplicate, are kept
    # Delete subsequent duplicates
    assert ThemeMapping.objects.count() == 3
    assert ThemeMapping.objects.filter(id=tm1.id).exists()
    assert ThemeMapping.objects.filter(id=duplicate0.id).exists()
    assert ThemeMapping.objects.filter(id=tm2.id).exists()
    assert not ThemeMapping.objects.filter(id=duplicate1.id).exists()
    assert not ThemeMapping.objects.filter(id=duplicate2.id).exists()

    # Cleanup:
    migrator.reset()


@pytest.mark.django_db
def test_0068_remove_respondent_demographics_and_more(migrator):
    """Test migration applies successfully"""

    # Start from previous migration
    old_state = migrator.apply_initial_migration(
        ("consultations", "0067_responseannotation_new_evidence_rich")
    )

    # Create test data before migration
    Consultation = old_state.apps.get_model("consultations", "Consultation")
    consultation = Consultation.objects.create(title="example", slug="example")

    Respondent = old_state.apps.get_model("consultations", "Respondent")
    respondent = Respondent.objects.create(consultation=consultation, demographics={"a": 1, "b": 2})

    # Apply the migration
    new_state = migrator.apply_tested_migration(
        ("consultations", "0068_remove_respondent_demographics_and_more"),
    )

    # Test the migration worked
    NewRespondent = new_state.apps.get_model("consultations", "Respondent")

    new_respondent = NewRespondent.objects.get(pk=respondent.pk)
    assert new_respondent.demographics.count() == 2
    assert list(new_respondent.demographics.values("field_name", "field_value")) == [
        {"field_name": "a", "field_value": "1"},
        {"field_name": "b", "field_value": "2"},
    ]


@pytest.mark.django_db
def test_0069_alter_demographicoption_field_value(migrator):
    """Test migration applies successfully"""

    test_values = [
        ("age-range", "45-55", "'45-55'"),
        ("string", "hello", "'hello'"),
        ("number", "12", "'12'"),
        ("bool", "True", True),
    ]

    # Start from previous migration
    old_state = migrator.apply_initial_migration(
        ("consultations", "0068_remove_respondent_demographics_and_more")
    )

    # Create test data before migration
    Consultation = old_state.apps.get_model("consultations", "Consultation")
    consultation = Consultation.objects.create(title="example", slug="example")
    OldDemographicOption = old_state.apps.get_model("consultations", "DemographicOption")

    for name, old_value, _ in test_values:
        OldDemographicOption.objects.create(
            consultation=consultation,
            field_name=name,
            field_value=old_value,
        )

    # Apply the migration
    new_state = migrator.apply_tested_migration(
        ("consultations", "0069_alter_demographicoption_field_value"),
    )

    # Test the migration worked
    NewDemographicOption = new_state.apps.get_model("consultations", "DemographicOption")
    for name, _, new_value in test_values:
        assert NewDemographicOption.objects.get(field_name=name).field_value == new_value


@pytest.mark.django_db()
def test_0094_historicalresponseannotationtheme_response_and_more(migrator):
    # Check group doesn't exist before migration
    old_state = migrator.apply_initial_migration(("consultations", "0093_consultation_model_name"))
    Consultation = old_state.apps.get_model("consultations", "Consultation")
    Question = old_state.apps.get_model("consultations", "Question")
    Respondent = old_state.apps.get_model("consultations", "Respondent")
    Response = old_state.apps.get_model("consultations", "Response")
    ResponseAnnotation = old_state.apps.get_model("consultations", "ResponseAnnotation")
    SelectedTheme = old_state.apps.get_model("consultations", "SelectedTheme")
    OldResponseAnnotationTheme = old_state.apps.get_model(
        "consultations", "ResponseAnnotationTheme"
    )

    consultation = Consultation.objects.create(title="example")
    question = Question.objects.create(consultation=consultation, number=1)
    respondent = Respondent.objects.create(consultation=consultation)
    response = Response.objects.create(respondent=respondent, question=question)
    response_annotation = ResponseAnnotation.objects.create(response=response)
    theme = SelectedTheme.objects.create(question=question, name="name", description="description")
    old_response_annotation_theme = OldResponseAnnotationTheme.objects.create(
        theme=theme, response_annotation=response_annotation
    )

    # Run the migration that creates the group
    new_state = migrator.apply_tested_migration(
        ("consultations", "0094_historicalresponseannotationtheme_response_and_more")
    )
    NewesponseAnnotationTheme = new_state.apps.get_model("consultations", "ResponseAnnotationTheme")
    new_response_annotation_theme = NewesponseAnnotationTheme.objects.get(
        pk=old_response_annotation_theme.pk
    )

    assert new_response_annotation_theme.response.pk == response.pk
    assert new_response_annotation_theme.theme.pk == theme.pk

    # Cleanup:
    migrator.reset()


@pytest.mark.django_db()
def test_0096_historicalresponse_evidence_rich_and_more(migrator):
    # Check group doesn't exist before migration
    old_state = migrator.apply_initial_migration(
        ("consultations", "0095_historicalresponse_and_more")
    )
    User = old_state.apps.get_model("authentication", "User")
    Consultation = old_state.apps.get_model("consultations", "Consultation")
    Question = old_state.apps.get_model("consultations", "Question")
    Respondent = old_state.apps.get_model("consultations", "Respondent")
    Response = old_state.apps.get_model("consultations", "Response")
    ResponseAnnotation = old_state.apps.get_model("consultations", "ResponseAnnotation")

    consultation = Consultation.objects.create(title="example")
    question = Question.objects.create(consultation=consultation, number=1)
    respondent = Respondent.objects.create(consultation=consultation)
    old_response = Response.objects.create(respondent=respondent, question=question)

    reviewer = User.objects.create(email="reviewer@example.com")
    now = datetime.now(timezone.utc)
    ResponseAnnotation.objects.create(
        response=old_response,
        evidence_rich=True,
        human_reviewed=True,
        reviewed_at=now,
        reviewed_by=reviewer,
        sentiment="DISAGREEMENT",
    )

    # Run the migration that creates the group
    new_state = migrator.apply_tested_migration(
        ("consultations", "0096_historicalresponse_evidence_rich_and_more")
    )
    NewResponse = new_state.apps.get_model("consultations", "Response")
    new_response = NewResponse.objects.get(pk=old_response.pk)

    assert new_response.evidence_rich is True
    assert new_response.human_reviewed is True
    assert new_response.reviewed_at == now
    assert new_response.reviewed_by.email == "reviewer@example.com"
    assert new_response.sentiment == "DISAGREEMENT"

    # Cleanup:
    migrator.reset()
