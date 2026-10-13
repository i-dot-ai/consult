from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import Consultation
from factories import ConsultationFactory, UserFactory


@pytest.mark.django_db
def test_v2_update_assigned_user_sets_data_source(client, consultation, non_staff_user_token):
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.patch(
        url,
        data={"data_source": "qualtrics"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert response.json()["data_source"] == "qualtrics"
    consultation.refresh_from_db()
    assert consultation.data_source == Consultation.DataSource.QUALTRICS


@pytest.mark.django_db
def test_v2_update_owner_not_assigned_sets_title(client, non_staff_user, non_staff_user_token):
    consultation = ConsultationFactory(created_by=non_staff_user)
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.patch(
        url,
        data={"title": "Renamed"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    consultation.refresh_from_db()
    assert consultation.title == "Renamed"


@pytest.mark.django_db
def test_v2_update_staff_user_sets_title_on_any_consultation(client, staff_user_token):
    consultation = ConsultationFactory(created_by=UserFactory())
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.patch(
        url,
        data={"title": "Renamed"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    consultation.refresh_from_db()
    assert consultation.title == "Renamed"


@pytest.mark.django_db
def test_v2_update_clears_data_source_with_null(client, consultation, non_staff_user_token):
    consultation.data_source = Consultation.DataSource.QUALTRICS
    consultation.save(update_fields=["data_source"])
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.patch(
        url,
        data={"data_source": None},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    consultation.refresh_from_db()
    assert consultation.data_source is None


@pytest.mark.django_db
def test_v2_update_rejects_blank_title(client, consultation, non_staff_user_token):
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.patch(
        url,
        data={"title": ""},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert "title" in response.json()
    consultation.refresh_from_db()
    assert consultation.title == "My First Consultation"


@pytest.mark.django_db
def test_v2_update_rejects_unknown_data_source(client, consultation, non_staff_user_token):
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.patch(
        url,
        data={"data_source": "typeform"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert "data_source" in response.json()
    consultation.refresh_from_db()
    assert consultation.data_source is None


@pytest.mark.django_db
def test_v2_update_ignores_read_only_fields(
    client, consultation, non_staff_user, non_staff_user_token
):
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})
    other_user = UserFactory()

    response = client.patch(
        url,
        data={
            "title": "Renamed",
            "code": "tampered",
            "stage": "analysis",
            "running_job": "find-themes",
            "started_at": "2026-01-01T00:00:00Z",
            "closed_at": "2026-02-01T00:00:00Z",
            "created_by": {"id": other_user.id},
            "users": [other_user.id],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    consultation.refresh_from_db()
    assert consultation.title == "Renamed"
    assert consultation.code == "my-first-consultation"
    assert consultation.stage == Consultation.Stage.SETUP
    assert consultation.running_job is None
    assert consultation.started_at is None
    assert consultation.closed_at is None
    assert consultation.created_by is None
    assert list(consultation.users.all()) == [non_staff_user]


@pytest.mark.django_db
def test_v2_update_saves_only_submitted_fields(client, consultation, non_staff_user_token):
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    with patch.object(Consultation, "save", autospec=True) as mock_save:
        response = client.patch(
            url,
            data={"title": "Renamed"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 200
    mock_save.assert_called_once()
    assert mock_save.call_args.kwargs["update_fields"] == ["title", "modified_at"]


@pytest.mark.django_db
def test_v2_update_with_no_writable_fields_does_not_save(
    client, consultation, non_staff_user_token
):
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    with patch.object(Consultation, "save", autospec=True) as mock_save:
        response = client.patch(
            url,
            data={"stage": "analysis"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 200
    mock_save.assert_not_called()


@pytest.mark.django_db
def test_v2_update_unassigned_user_returns_403(client, consultation):
    other_user = UserFactory(is_staff=False)
    token = str(RefreshToken.for_user(other_user).access_token)
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.patch(
        url,
        data={"title": "Renamed"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    consultation.refresh_from_db()
    assert consultation.title != "Renamed"


@pytest.mark.django_db
def test_v2_update_unauthenticated_returns_401(client, consultation):
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.patch(url, data={"title": "Renamed"}, content_type="application/json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_v2_update_put_not_allowed(client, consultation, non_staff_user_token):
    url = reverse("consultation-v2-detail", kwargs={"pk": consultation.id})

    response = client.put(
        url,
        data={"title": "Renamed"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 405
