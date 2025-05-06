import pytest

from consultation_analyser.constants import DASHBOARD_ACCESS


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
