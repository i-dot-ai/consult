import pytest
from django.test import override_settings
from django.urls import reverse

V2_ROOT_URL = reverse("data-setup-v2-root")


@pytest.mark.django_db
@override_settings(DATA_SETUP_V2_ENABLED=False)
def test_v2_routes_not_reachable_when_disabled(client, staff_user):
    client.force_login(staff_user)
    assert client.get(V2_ROOT_URL).status_code == 404


@pytest.mark.django_db
@override_settings(DATA_SETUP_V2_ENABLED=False)
def test_v2_routes_hidden_before_auth_when_disabled(client):
    assert client.get(V2_ROOT_URL).status_code == 404


@pytest.mark.django_db
@override_settings(DATA_SETUP_V2_ENABLED=True)
def test_v2_routes_reachable_when_enabled(client, staff_user):
    client.force_login(staff_user)
    assert client.get(V2_ROOT_URL).status_code == 200
