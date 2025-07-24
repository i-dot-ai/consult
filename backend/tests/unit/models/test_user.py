import pytest
from django.contrib.auth.models import Group

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_user_has_dashboard_access():
    user = UserFactory()
    assert not user.has_dashboard_access
    dash_access, created = Group.objects.get_or_create(name=DASHBOARD_ACCESS)
    user.groups.add(dash_access)
    user.save()
    assert user.has_dashboard_access
