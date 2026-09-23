import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from factories import UserFactory


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
