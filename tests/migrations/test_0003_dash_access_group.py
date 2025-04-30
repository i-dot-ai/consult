import pytest


@pytest.mark.django_db()
def test_0003_dashboard_permission(migrator):
    # Check group doesn't exist before migration
    old_state = migrator.apply_initial_migration(("authentication", "0002_insert_user"))
    Group = old_state.apps.get_model("auth", "Group")
    assert not Group.objects.filter(name="Dashboard access").exists()

    # Run the migration that creates the group
    new_state = migrator.apply_tested_migration(("authentication", "0003_dashboard_permission"))

    # Verify that the group is created successfully
    Group = new_state.apps.get_model("auth", "Group")
    assert Group.objects.filter(name="Dashboard access").exists()

    # Cleanup:
    migrator.reset()
