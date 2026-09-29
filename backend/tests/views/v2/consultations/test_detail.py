import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from factories import ConsultationFactory, UserFactory


@pytest.mark.django_db
def test_v2_detail_visible_to_assigned_user(client, non_staff_user_token, consultation):
    url = reverse("consultation-v2-detail", args=[consultation.id])

    response = client.get(url, headers={"Authorization": f"Bearer {non_staff_user_token}"})

    assert response.status_code == 200
    assert response.json()["id"] == str(consultation.id)


@pytest.mark.django_db
def test_v2_detail_returns_created_by(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)
    consultation.users.add(non_staff_user)
    url = reverse("consultation-v2-detail", args=[consultation.id])

    response = client.get(url, headers={"Authorization": f"Bearer {non_staff_user_token}"})

    assert response.status_code == 200
    assert response.json()["created_by"]["id"] == non_staff_user.id


@pytest.mark.django_db
def test_v2_detail_created_by_null_when_ownerless(client, non_staff_user_token, consultation):
    url = reverse("consultation-v2-detail", args=[consultation.id])

    response = client.get(url, headers={"Authorization": f"Bearer {non_staff_user_token}"})

    assert response.status_code == 200
    assert response.json()["created_by"] is None


@pytest.mark.django_db
def test_v2_detail_visible_to_superuser_when_not_assigned(client, staff_user_token):
    consultation = ConsultationFactory(created_by=UserFactory())
    url = reverse("consultation-v2-detail", args=[consultation.id])

    response = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

    assert response.status_code == 200
    assert response.json()["id"] == str(consultation.id)


@pytest.mark.django_db
def test_v2_detail_forbidden_for_unassigned_user(client, consultation):
    other_user = UserFactory(is_staff=False)
    token = str(RefreshToken.for_user(other_user).access_token)
    url = reverse("consultation-v2-detail", args=[consultation.id])

    response = client.get(url, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


@pytest.mark.django_db
def test_v2_detail_rejects_unauthenticated(client, consultation):
    response = client.get(reverse("consultation-v2-detail", args=[consultation.id]))

    assert response.status_code == 401
