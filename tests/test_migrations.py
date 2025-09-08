import pytest


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
