from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from factories import ConsultationFactory, UserFactory


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
def test_v2_list_returns_dates_and_ownership(client, non_staff_user, non_staff_user_token):
    started = timezone.now() - timedelta(days=30)
    closed = timezone.now() - timedelta(days=1)
    consultation = ConsultationFactory(
        title="Owned Consultation",
        created_by=non_staff_user,
        started_at=started,
        closed_at=closed,
    )
    consultation.users.add(non_staff_user)

    response = client.get(
        reverse("consultation-v2-list"),
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    [result] = response.json()["results"]
    assert result["title"] == "Owned Consultation"
    assert result["created_by"]["id"] == non_staff_user.id
    assert result["started_at"] is not None
    assert result["closed_at"] is not None
    assert result["is_owner"] is True
    assert result["is_assigned"] is True


@pytest.mark.django_db
def test_v2_list_marks_ownerless_consultation(client, non_staff_user_token, consultation):
    # The consultation fixture has no creator (created_by is SET_NULL), so is_owner is None
    # rather than False to distinguish "no owner" from "owned by someone else".
    response = client.get(
        reverse("consultation-v2-list"),
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    [result] = response.json()["results"]
    assert result["is_owner"] is None
    assert result["is_assigned"] is True
    assert result["closed_at"] is None


@pytest.mark.django_db
def test_v2_list_marks_owned_by_another_user(client, staff_user, staff_user_token):
    other_owner = UserFactory(is_staff=False)
    consultation = ConsultationFactory(title="Someone Else's", created_by=other_owner)

    response = client.get(
        reverse("consultation-v2-list"),
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    [result] = response.json()["results"]
    assert result["id"] == str(consultation.id)
    assert result["is_owner"] is False
    assert result["is_assigned"] is False


@pytest.mark.django_db
def test_v2_list_marks_owned_but_not_assigned(client, staff_user, staff_user_token):
    consultation = ConsultationFactory(title="Staff Owned", created_by=staff_user)

    response = client.get(
        reverse("consultation-v2-list"),
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    [result] = response.json()["results"]
    assert result["id"] == str(consultation.id)
    assert result["is_owner"] is True
    assert result["is_assigned"] is False


@pytest.mark.django_db
def test_v2_list_filters_by_title_case_insensitively(client, non_staff_user, non_staff_user_token):
    match = ConsultationFactory(title="Future Homes Standard", created_by=non_staff_user)
    match.users.add(non_staff_user)
    other = ConsultationFactory(title="Building Safety Levy", created_by=non_staff_user)
    other.users.add(non_staff_user)

    response = client.get(
        reverse("consultation-v2-list"),
        {"title__iexact": "future homes standard"},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert [c["id"] for c in body["results"]] == [str(match.id)]


@pytest.mark.django_db
def test_v2_list_title_filter_excludes_consultations_user_cannot_see(client, non_staff_user_token):
    ConsultationFactory(title="Someone Elses Consultation")

    response = client.get(
        reverse("consultation-v2-list"),
        {"title__iexact": "someone elses consultation"},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["count"] == 0
