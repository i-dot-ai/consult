import pytest
from django.test import override_settings
from django.urls import reverse

from consultations.api.schema import hide_disabled_v2_endpoints

V2_ROOT_URL = reverse("data-setup-v2-root")

# drf-spectacular hands preprocessing hooks a list of
# (path, path_regex, method, callback) tuples.
SCHEMA_ENDPOINTS = [
    ("/api/consultations/", None, "GET", None),
    ("/api/v2/", None, "GET", None),
]


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


@override_settings(DATA_SETUP_V2_ENABLED=False)
def test_v2_dropped_from_schema_when_disabled():
    kept = hide_disabled_v2_endpoints(SCHEMA_ENDPOINTS)
    assert kept == [("/api/consultations/", None, "GET", None)]


@override_settings(DATA_SETUP_V2_ENABLED=True)
def test_v2_kept_in_schema_when_enabled():
    assert hide_disabled_v2_endpoints(SCHEMA_ENDPOINTS) == SCHEMA_ENDPOINTS
