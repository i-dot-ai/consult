import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
class TestCurrentUserAPIView:
    """Test the /api/user/me/ endpoint"""

    def test_authenticated_user_basic_info(self, client):
        """Test that authenticated user receives their basic information"""
        user = UserFactory(email="test@example.com")
        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == user.id
        assert data["email"] == "test@example.com"
        assert data["is_staff"] is False
        assert data["has_dashboard_access"] is False

    def test_authenticated_staff_user(self, client):
        """Test that staff user has correct staff status"""
        user = UserFactory(email="staff@example.com", is_staff=True)
        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == user.id
        assert data["email"] == "staff@example.com"
        assert data["is_staff"] is True
        assert data["has_dashboard_access"] is False

    def test_authenticated_user_with_dashboard_access(self, client):
        """Test that user with dashboard access has correct permissions"""
        user = UserFactory(email="dashboard@example.com")
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == user.id
        assert data["email"] == "dashboard@example.com"
        assert data["is_staff"] is False
        assert data["has_dashboard_access"] is True

    def test_authenticated_staff_user_with_dashboard_access(self, client):
        """Test that staff user with dashboard access has both permissions"""
        user = UserFactory(email="admin@example.com", is_staff=True)
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == user.id
        assert data["email"] == "admin@example.com"
        assert data["is_staff"] is True
        assert data["has_dashboard_access"] is True

    def test_unauthenticated_user_denied(self, client):
        """Test that unauthenticated users cannot access the endpoint"""
        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "Authentication credentials" in data["detail"]

    def test_serializer_contains_only_expected_fields(self, client):
        """Test that the serializer only exposes expected user fields"""
        user = UserFactory(email="test@example.com")
        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        # Check that only expected fields are present
        expected_fields = {"id", "email", "is_staff", "has_dashboard_access"}
        actual_fields = set(data.keys())
        assert actual_fields == expected_fields

        # Ensure sensitive fields are not exposed
        sensitive_fields = {"password", "last_login", "date_joined", "is_superuser"}
        for field in sensitive_fields:
            assert field not in data

    def test_email_case_normalization(self, client):
        """Test that email is returned as stored (case preserved)"""
        user = UserFactory(email="Test.User@Example.COM")
        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        # Email should be returned exactly as stored
        assert data["email"] == "Test.User@Example.COM"

    def test_multiple_sessions_same_user(self, client):
        """Test that the endpoint works correctly with multiple sessions"""
        user = UserFactory(email="multi@example.com")

        # First session
        client.force_login(user)
        url = reverse("current_user")
        response1 = client.get(url)

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["email"] == "multi@example.com"

        # Logout and login again (simulating new session)
        client.logout()
        client.force_login(user)
        response2 = client.get(url)

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["email"] == "multi@example.com"
        assert data1["id"] == data2["id"]  # Same user ID

    def test_user_permissions_change_reflected_immediately(self, client):
        """Test that permission changes are reflected immediately"""
        user = UserFactory(email="changing@example.com")
        client.force_login(user)

        url = reverse("current_user")

        # Initially no dashboard access
        response1 = client.get(url)
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["has_dashboard_access"] is False

        # Add dashboard access
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        # Should immediately reflect the change
        response2 = client.get(url)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["has_dashboard_access"] is True

        # Remove dashboard access
        user.groups.remove(dash_access)
        user.save()

        # Should immediately reflect the removal
        response3 = client.get(url)
        assert response3.status_code == 200
        data3 = response3.json()
        assert data3["has_dashboard_access"] is False


@pytest.mark.django_db
class TestUserSerializerBehavior:
    """Test the UserSerializer behavior in isolation"""

    def test_serializer_with_inactive_user(self, client):
        """Test that inactive users cannot access the API (Django's built-in protection)"""
        user = UserFactory(email="inactive@example.com", is_active=False)
        # Django's authentication system prevents login for inactive users
        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        # Django's IsAuthenticated permission should deny inactive users
        assert response.status_code == 403

    def test_serializer_readonly_fields(self, client):
        """Test that readonly fields work correctly"""
        user = UserFactory(email="readonly@example.com")
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        # has_dashboard_access should be readonly and computed
        assert data["has_dashboard_access"] is True

        # It should reflect the actual database state
        user.groups.clear()
        user.save()

        response2 = client.get(url)
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["has_dashboard_access"] is False


@pytest.mark.django_db
class TestUserAPIIntegration:
    """Test integration scenarios for the user API"""

    def test_api_endpoint_matches_session_user(self, client):
        """Test that the API endpoint returns data for the session user"""
        user1 = UserFactory(email="user1@example.com")
        user2 = UserFactory(email="user2@example.com")

        # Login as user1
        client.force_login(user1)
        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user1@example.com"
        assert data["id"] == user1.id

        # Switch to user2
        client.force_login(user2)
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user2@example.com"
        assert data["id"] == user2.id

    def test_api_endpoint_with_special_characters_in_email(self, client):
        """Test that emails with special characters work correctly"""
        user = UserFactory(email="test+tag@example-domain.co.uk")
        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test+tag@example-domain.co.uk"

    def test_api_response_format(self, client):
        """Test that the API response format is correct"""
        user = UserFactory(email="format@example.com")
        client.force_login(user)

        url = reverse("current_user")
        response = client.get(url)

        assert response.status_code == 200
        assert response.get("Content-Type") == "application/json; charset=utf-8"

        data = response.json()

        # Verify data types
        assert isinstance(data["id"], int)
        assert isinstance(data["email"], str)
        assert isinstance(data["is_staff"], bool)
        assert isinstance(data["has_dashboard_access"], bool)

    def test_concurrent_requests_same_user(self, client):
        """Test that concurrent requests for the same user work correctly"""
        user = UserFactory(email="concurrent@example.com")
        client.force_login(user)

        url = reverse("current_user")

        # Simulate multiple concurrent requests
        responses = [client.get(url) for _ in range(5)]

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "concurrent@example.com"
            assert data["id"] == user.id
