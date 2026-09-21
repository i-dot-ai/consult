import importlib

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import NoReverseMatch, clear_url_caches, reverse
from rest_framework_simplejwt.tokens import RefreshToken

from factories import UserFactory


@pytest.fixture
def reload_urlconf():
    """Reload the root URLconf so a DATA_SETUP_V2_ENABLED override takes effect.

    The v2 include is decided at URLconf import time, so override_settings alone
    won't add or drop the routes without rebuilding the resolver.
    """

    def _reload():
        clear_url_caches()
        importlib.reload(importlib.import_module(settings.ROOT_URLCONF))

    yield _reload
    _reload()


@pytest.mark.django_db
def test_v2_consultations_visible_to_assigned_user(client, non_staff_user_token, consultation):
    url = reverse("consultation-v2-list")

    response = client.get(url, headers={"Authorization": f"Bearer {non_staff_user_token}"})

    assert response.status_code == 200
    assert [c["id"] for c in response.json()["results"]] == [str(consultation.id)]


@pytest.mark.django_db
def test_v2_consultations_hidden_from_unassigned_user(client, consultation):
    other_user = UserFactory(is_staff=False)
    token = str(RefreshToken.for_user(other_user).access_token)
    url = reverse("consultation-v2-list")

    response = client.get(url, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_v2_consultations_reject_unauthenticated(client):
    response = client.get(reverse("consultation-v2-list"))

    assert response.status_code == 401


@pytest.mark.django_db
def test_v2_routes_absent_when_flag_off(client, reload_urlconf):
    with override_settings(DATA_SETUP_V2_ENABLED=False):
        reload_urlconf()

        assert client.get("/api/v2/consultations/").status_code == 404
        with pytest.raises(NoReverseMatch):
            reverse("consultation-v2-list")
