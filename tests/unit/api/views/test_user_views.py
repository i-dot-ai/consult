import json

import pytest
from django.urls import reverse

from consultation_analyser.consultations.models import User


@pytest.mark.django_db
class TestUserViewSet:
    def test_users_list(self, client, consultation_user_token):
        url = reverse("user-list")
        response = client.get(
            url,
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        assert response.json()["count"] == 3

    def test_users_detail(self, client, consultation_user, consultation_user_token):
        url = reverse(
            "user-detail",
            kwargs={"pk": consultation_user.pk},
        )
        response = client.get(
            url,
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        assert response.json()["email"] == consultation_user.email

    def test_users_delete(self, client, consultation_user, consultation_user_token):
        url = reverse(
            "user-detail",
            kwargs={"pk": consultation_user.pk},
        )
        response = client.delete(
            url,
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 204
        assert not User.objects.filter(pk=consultation_user.pk).exists()

    def test_users_create(self, client, consultation_user_token):
        email = "Test@Example.com"
        assert not User.objects.filter(email="test@example.com").exists()
        url = reverse("user-list")
        response = client.post(
            url,
            data={"email": email},
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 201
        assert User.objects.get(id=response.json()["id"]).email == email.lower()

    def test_users_bulk_create_success(self, client, consultation_user_token):
        emails = [f"bulkuser{i}@example.com" for i in range(1, 4)]
        url = reverse("user-list")
        response = client.post(
            url,
            data=json.dumps({"emails": emails}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 201
        assert User.objects.filter(email="bulkuser1@example.com").exists()
        assert User.objects.filter(email="bulkuser2@example.com").exists()
        assert User.objects.filter(email="bulkuser3@example.com").exists()

    def test_users_bulk_create_failure(self, client, consultation_user_token):
        User.objects.create(email="existing@example.com")
        emails = ["existing@example.com", "newuser@example.com", "invalid-email"]
        url = reverse("user-list")
        response = client.post(
            url,
            data=json.dumps({"emails": emails, "has_dashboard_access": True}),
            content_type="application/json",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 400
        assert User.objects.filter(email="newuser@example.com").exists()
        assert response.json() == {
            "detail": "Some users not created.",
            "errors": [
                {
                    "email": "existing@example.com",
                    "errors": {"email": ["user with this email address already exists."]},
                },
                {"email": "invalid-email", "errors": {"email": ["Enter a valid email address."]}},
            ],
        }

    def test_users_patch(self, client, consultation_user, consultation_user_token):
        assert consultation_user.has_dashboard_access is True
        url = reverse(
            "user-detail",
            kwargs={"pk": consultation_user.pk},
        )
        response = client.patch(
            url,
            data=json.dumps({"has_dashboard_access": False}),
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        assert response.json()["has_dashboard_access"] is False
        consultation_user.refresh_from_db()
        assert consultation_user.has_dashboard_access is False

    def test_users_patch_fail(self, client, consultation_user, consultation_user_token):
        assert consultation_user.is_staff is True
        url = reverse(
            "user-detail",
            kwargs={"pk": consultation_user.pk},
        )
        response = client.patch(
            url,
            data=json.dumps({"is_staff": False}),
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 400
        assert "You cannot remove admin privileges from yourself" in response.json()["is_staff"]

    def test_user_consultations_success(
        self, client, consultation_user, consultation, consultation_user_token
    ):
        """Test that admin can access user's consultations"""
        url = reverse(
            "user-consultations",
            kwargs={"pk": consultation_user.pk},
        )
        response = client.get(
            url,
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == str(consultation.id)
        assert data[0]["title"] == consultation.title

    def test_user_consultations_no_consultations(
        self, client, non_consultation_user, consultation_user_token
    ):
        """Test that endpoint returns empty list for user with no consultations"""
        url = reverse(
            "user-consultations",
            kwargs={"pk": non_consultation_user.pk},
        )
        response = client.get(
            url,
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_user_consultations_requires_admin(
        self, client, consultation_user, non_consultation_user_token
    ):
        """Test that non-admin users cannot access this endpoint"""
        url = reverse(
            "user-consultations",
            kwargs={"pk": consultation_user.pk},
        )
        response = client.get(
            url,
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {non_consultation_user_token}",
            },
        )
        assert response.status_code == 403

    def test_user_consultations_user_not_found(self, client, consultation_user_token):
        """Test that endpoint returns 404 for non-existent user"""
        url = reverse(
            "user-consultations",
            kwargs={"pk": 99999},
        )
        response = client.get(
            url,
            content_type="application/json",
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 404
