from uuid import uuid4

import pytest
from django.urls import reverse
from magic_link.models import MagicLink
from rest_framework_simplejwt.tokens import RefreshToken


@pytest.mark.django_db
def test_token_magic_link(client, dashboard_user):
    url = reverse("token-magic-link")
    response = client.post(url, data={"email": dashboard_user.email})
    assert response.status_code == 200
    assert response.json() == {"message": "Magic link sent"}


@pytest.mark.django_db
def test_token_magic_link_fail(client, dashboard_user):
    url = reverse("token-magic-link")
    response = client.post(url, data={"user": dashboard_user.email})
    assert response.status_code == 400
    assert response.json() == {"detail": "Email required"}


@pytest.mark.django_db
def test_create_token(client, dashboard_user):
    link = MagicLink.objects.create(user=dashboard_user)
    url = reverse("create-token")
    response = client.post(url, data={"token": link.token})
    assert response.status_code == 200
    assert "access" in response.json()
    assert "refresh" in response.json()


@pytest.mark.django_db
def test_create_token_fail(client):
    token = uuid4()
    url = reverse("create-token")
    response = client.post(url, data={"token": token})
    assert response.status_code == 404
    assert response.json() == {"detail": "No MagicLink matches the given query."}


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_pattern",
    [
        "question-demographic-options",
        "question-demographic-aggregations",
        "question-theme-information",
        "question-theme-aggregations",
        "question-filtered-responses",
        "question-detail",
    ],
)
def test_api_urls_permission_required(
    client,
    dashboard_user,
    question,
    dashboard_user_token,
    url_pattern,
    non_consultation_user_token,
    non_dashboard_user_token,
):
    """
    Test API endpoints return 403 for authentication/permission failures.

    API endpoints use DRF permissions which return 403 (Forbidden) rather than
    404 (Not Found) for unauthorized access.
    """
    url = reverse(
        viewname=url_pattern,
        kwargs={"consultation_pk": question.consultation.pk, "pk": question.pk},
    )

    # Not logged in - should return 401 (DRF un-authenticated)
    assert client.get(url).status_code == 401

    # Logged in with a user for this consultation - 200
    response = client.get(url, headers={"Authorization": f"Bearer {dashboard_user_token}"})
    assert response.status_code == 200

    # Logged in with a different user (no consultation access) - 403
    response = client.get(url, headers={"Authorization": f"Bearer {non_consultation_user_token}"})
    assert response.status_code == 403

    # Logged in with user without dashboard access - 403
    response = client.get(url, headers={"Authorization": f"Bearer {non_dashboard_user_token}"})
    assert response.status_code == 403


@pytest.mark.django_db
def test_refresh(client, dashboard_user):
    refresh = RefreshToken.for_user(dashboard_user)
    url = reverse("refresh-token")

    response = client.post(url, data={"refresh": str(refresh)})
    assert response.status_code == 200, response.content
    assert set(response.json()) == {"access"}

    assert response.json()["access"] != str(refresh.token)
