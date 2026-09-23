import importlib

import pytest
from django.conf import settings
from django.test import override_settings
from django.urls import NoReverseMatch, clear_url_caches, reverse
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import Consultation
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
def test_v2_create_consultation_returns_id_and_assigns_creator(
    client, non_staff_user, non_staff_user_token
):
    url = reverse("consultation-v2-list")

    response = client.post(
        url,
        data={"title": "New Consultation"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["title"] == "New Consultation"

    consultation = Consultation.objects.get(id=body["id"])
    assert non_staff_user in consultation.users.all()
    assert consultation.created_by == non_staff_user


@pytest.mark.django_db
def test_v2_create_consultation_allows_duplicate_title(client, non_staff_user_token):
    url = reverse("consultation-v2-list")

    first = client.post(
        url,
        data={"title": "Same Title"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )
    second = client.post(
        url,
        data={"title": "Same Title"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


@pytest.mark.django_db
def test_v2_create_consultation_rejects_unauthenticated(client):
    response = client.post(
        reverse("consultation-v2-list"),
        data={"title": "New Consultation"},
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_v2_routes_absent_when_flag_off(client, reload_urlconf):
    with override_settings(DATA_SETUP_V2_ENABLED=False):
        reload_urlconf()

        assert client.get("/api/v2/consultations/").status_code == 404
        with pytest.raises(NoReverseMatch):
            reverse("consultation-v2-list")
