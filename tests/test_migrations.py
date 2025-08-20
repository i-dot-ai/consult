import pytest


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
