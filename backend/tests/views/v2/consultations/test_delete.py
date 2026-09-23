from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import Consultation
from factories import ConsultationFactory, UserFactory


@pytest.mark.django_db
def test_v2_delete_consultation_assigned_user_returns_202(
    client, consultation, non_staff_user_token
):
    """An assigned user can queue deletion and gets 202 with a confirmation body."""
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    with patch("ingest.jobs.delete_consultation_job.delay") as mock_delay:
        response = client.delete(url, headers={"Authorization": f"Bearer {non_staff_user_token}"})

    assert response.status_code == 202
    body = response.json()
    assert "queued" in body["message"]
    assert body["consultation_id"] == str(consultation.id)
    mock_delay.assert_called_once_with(consultation.id)

    # Consultation must still exist — worker handles actual deletion
    assert Consultation.objects.filter(pk=consultation.pk).exists()


@pytest.mark.django_db
def test_v2_delete_consultation_owner_returns_202(client, non_staff_user, non_staff_user_token):
    """The owner (created_by) can queue deletion even if not in users M2M."""
    consultation = ConsultationFactory(created_by=non_staff_user)
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    with patch("ingest.jobs.delete_consultation_job.delay") as mock_delay:
        response = client.delete(url, headers={"Authorization": f"Bearer {non_staff_user_token}"})

    assert response.status_code == 202
    mock_delay.assert_called_once_with(consultation.id)
    assert Consultation.objects.filter(pk=consultation.pk).exists()


@pytest.mark.django_db
def test_v2_delete_consultation_staff_user_returns_202(client, consultation, staff_user_token):
    """A staff (superuser) user can queue deletion of any consultation."""
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    with patch("ingest.jobs.delete_consultation_job.delay") as mock_delay:
        response = client.delete(url, headers={"Authorization": f"Bearer {staff_user_token}"})

    assert response.status_code == 202
    mock_delay.assert_called_once_with(consultation.id)


@pytest.mark.django_db
def test_v2_delete_consultation_unassigned_user_returns_403(client, consultation):
    """A user with no relationship to the consultation is denied."""
    other_user = UserFactory(is_staff=False)
    token = str(RefreshToken.for_user(other_user).access_token)
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.delete(url, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert Consultation.objects.filter(pk=consultation.pk).exists()


@pytest.mark.django_db
def test_v2_delete_consultation_unauthenticated_returns_401(client, consultation):
    """Unauthenticated requests are rejected before reaching the view."""
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.delete(url)

    assert response.status_code == 401
    assert Consultation.objects.filter(pk=consultation.pk).exists()
