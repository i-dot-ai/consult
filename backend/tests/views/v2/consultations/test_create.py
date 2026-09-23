import pytest
from django.urls import reverse

from consultations.models import Consultation


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
