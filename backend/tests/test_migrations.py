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
def test_0008_lowercase_email_field(migrator):
    old_state = migrator.apply_initial_migration(
        ("authentication", "0007_remove_user_has_dashboard_access")
    )
    User = old_state.apps.get_model("authentication", "User")
    user = User.objects.create(email="Mixed.Case@example.com", password="")
    first_duplicate = User.objects.create(email="Dup.Account@example.com", password="")
    second_duplicate = User.objects.create(email="dup.account@example.com", password="")

    new_state = migrator.apply_tested_migration(("authentication", "0008_lowercase_email_field"))

    User = new_state.apps.get_model("authentication", "User")
    assert User.objects.get(pk=user.pk).email == "mixed.case@example.com"
    assert User.objects.get(pk=first_duplicate.pk).email == "Dup.Account@example.com"
    assert User.objects.get(pk=second_duplicate.pk).email == "dup.account@example.com"

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


def _legacy_consultation_before_0115(old_state):
    """A closed question, a hybrid split into an open question and its closed sibling, and
    one respondent whose selected options still live in the legacy tables."""
    Consultation = old_state.apps.get_model("consultations", "Consultation")
    Question = old_state.apps.get_model("consultations", "Question")
    Respondent = old_state.apps.get_model("consultations", "Respondent")
    Response = old_state.apps.get_model("consultations", "Response")
    MultiChoiceAnswer = old_state.apps.get_model("consultations", "MultiChoiceAnswer")
    SelectedOption = old_state.apps.get_model("consultations", "Response_chosen_options")

    consultation = Consultation.objects.create(title="Legacy")
    closed_question = Question.objects.create(
        consultation=consultation, text="Agree?", number=1, type="closed"
    )
    sibling = Question.objects.create(
        consultation=consultation, text="Why? (option)", number=3, type="closed"
    )
    open_question = Question.objects.create(
        consultation=consultation, text="Why?", number=2, type="open", closed_question=sibling
    )
    respondent = Respondent.objects.create(consultation=consultation)

    def select(question, option_texts, already_converted=()):
        response = Response.objects.create(question=question, respondent=respondent)
        for text in option_texts:
            option = MultiChoiceAnswer.objects.create(question=question, text=text)
            SelectedOption.objects.create(response=response, multichoiceanswer=option)
        for text in already_converted:
            Response.objects.create(
                question=question if question.type == "closed" else sibling,
                respondent=respondent,
                text=text,
            )

    select(closed_question, ["Yes", "No"], already_converted=["Yes"])
    select(open_question, ["Maybe"])
    return consultation, respondent, closed_question, sibling


@pytest.mark.django_db()
def test_0115_carries_selected_options_to_rows_before_dropping_the_tables(migrator):
    old_state = migrator.apply_initial_migration(
        ("consultations", "0114_consultation_is_v1_and_migrated_at")
    )
    _, respondent, closed_question, sibling = _legacy_consultation_before_0115(old_state)

    new_state = migrator.apply_tested_migration(("consultations", "0115_remove_multichoiceanswer"))

    Response = new_state.apps.get_model("consultations", "Response")
    rows = Response.objects.filter(respondent_id=respondent.id, text__isnull=False)
    assert sorted(rows.values_list("question_id", "text")) == sorted(
        [(closed_question.id, "Yes"), (closed_question.id, "No"), (sibling.id, "Maybe")]
    )
    assert not hasattr(Response, "chosen_options")

    Question = new_state.apps.get_model("consultations", "Question")
    counts = {
        question.number: (question.total_response_count, question.multi_choice_response_count)
        for question in Question.objects.all()
    }
    assert counts == {1: (1, 1), 2: (1, 1), 3: (1, 1)}

    migrator.reset()


@pytest.mark.django_db()
def test_0115_skips_a_selected_option_with_no_text(migrator):
    old_state = migrator.apply_initial_migration(
        ("consultations", "0114_consultation_is_v1_and_migrated_at")
    )
    _, respondent, closed_question, _ = _legacy_consultation_before_0115(old_state)
    Response = old_state.apps.get_model("consultations", "Response")
    MultiChoiceAnswer = old_state.apps.get_model("consultations", "MultiChoiceAnswer")
    SelectedOption = old_state.apps.get_model("consultations", "Response_chosen_options")
    legacy_response = Response.objects.get(
        question_id=closed_question.id, respondent_id=respondent.id, text__isnull=True
    )
    SelectedOption.objects.create(
        response=legacy_response,
        multichoiceanswer=MultiChoiceAnswer.objects.create(question=closed_question, text=""),
    )

    new_state = migrator.apply_tested_migration(("consultations", "0115_remove_multichoiceanswer"))

    Response = new_state.apps.get_model("consultations", "Response")
    assert sorted(
        Response.objects.filter(question_id=closed_question.id, text__isnull=False).values_list(
            "text", flat=True
        )
    ) == ["No", "Yes"]

    migrator.reset()


@pytest.mark.django_db()
def test_0115_refuses_selected_options_with_no_closed_question_to_hold_them(migrator):
    old_state = migrator.apply_initial_migration(
        ("consultations", "0114_consultation_is_v1_and_migrated_at")
    )
    consultation, respondent, _, _ = _legacy_consultation_before_0115(old_state)
    Question = old_state.apps.get_model("consultations", "Question")
    Response = old_state.apps.get_model("consultations", "Response")
    MultiChoiceAnswer = old_state.apps.get_model("consultations", "MultiChoiceAnswer")
    SelectedOption = old_state.apps.get_model("consultations", "Response_chosen_options")
    untyped = Question.objects.create(consultation=consultation, text="Untyped", number=9)
    response = Response.objects.create(question=untyped, respondent=respondent)
    SelectedOption.objects.create(
        response=response,
        multichoiceanswer=MultiChoiceAnswer.objects.create(question=untyped, text="Odd"),
    )

    with pytest.raises(RuntimeError, match="1 selected options sit on questions"):
        migrator.apply_tested_migration(("consultations", "0115_remove_multichoiceanswer"))

    # reset replays 0115, which only passes once the orphan is gone
    untyped.delete()
    migrator.reset()
