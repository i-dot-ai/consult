import pytest
from django.urls import reverse

from authentication.models import User
from factories import UserFactory


@pytest.mark.django_db
def test_v2_create_user_by_superuser(client, staff_user_token):
    url = reverse("user-v2-list")

    response = client.post(
        url,
        data={"email": "new.user@example.com"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new.user@example.com"
    assert body["is_staff"] is False
    assert User.objects.filter(email="new.user@example.com").exists()


@pytest.mark.django_db
def test_v2_create_user_lowercases_email(client, staff_user_token):
    url = reverse("user-v2-list")

    response = client.post(
        url,
        data={"email": "Mixed.Case@Example.com"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "mixed.case@example.com"


@pytest.mark.django_db
def test_v2_create_users_bulk(client, staff_user_token):
    url = reverse("user-v2-list")

    response = client.post(
        url,
        data={"emails": ["one@example.com", "two@example.com"]},
        content_type="application/json",
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 201
    assert {u["email"] for u in response.json()} == {"one@example.com", "two@example.com"}
    assert User.objects.filter(email__in=["one@example.com", "two@example.com"]).count() == 2


@pytest.mark.django_db
def test_v2_create_users_bulk_partial_failure(client, staff_user_token):
    UserFactory(email="taken@example.com")
    url = reverse("user-v2-list")

    response = client.post(
        url,
        data={"emails": ["fresh@example.com", "taken@example.com"]},
        content_type="application/json",
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    # Matches v1: valid emails are still created, and the 400 lists the failures.
    assert response.status_code == 400
    assert [e["email"] for e in response.json()["errors"]] == ["taken@example.com"]
    assert User.objects.filter(email="fresh@example.com").exists()


@pytest.mark.django_db
def test_v2_create_user_duplicate_email_rejected(client, staff_user_token):
    UserFactory(email="taken@example.com")
    url = reverse("user-v2-list")

    response = client.post(
        url,
        data={"email": "taken@example.com"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_v2_create_user_forbidden_for_non_staff(client, non_staff_user_token):
    url = reverse("user-v2-list")

    response = client.post(
        url,
        data={"email": "blocked@example.com"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 403
    assert not User.objects.filter(email="blocked@example.com").exists()


@pytest.mark.django_db
def test_v2_create_user_rejects_unauthenticated(client):
    response = client.post(
        reverse("user-v2-list"),
        data={"email": "anon@example.com"},
        content_type="application/json",
    )

    assert response.status_code == 401
