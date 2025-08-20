import pytest

from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_user_has_dashboard_access(dashboard_access_group):
    user = UserFactory()
    assert not user.has_dashboard_access
    user.groups.add(dashboard_access_group)
    user.save()
    assert user.has_dashboard_access
