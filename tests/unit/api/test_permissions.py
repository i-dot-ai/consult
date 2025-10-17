from unittest.mock import Mock

import pytest

from consultation_analyser.consultations.api.permissions import (
    CanSeeConsultation,
    HasDashboardAccess,
)
from consultation_analyser.factories import UserFactory
from tests.utils import build_url


@pytest.mark.django_db
class TestHasDashboardAccess:
    def test_authenticated_user_with_dashboard_access(self, request_factory, dashboard_user):
        """Test that authenticated user with dashboard access is granted permission"""
        request = request_factory.get("/")
        request.user = dashboard_user

        permission = HasDashboardAccess()
        assert permission.has_permission(request, None) is True

    def test_authenticated_user_without_dashboard_access(self, request_factory, non_dashboard_user):
        """Test that authenticated user without dashboard access is denied permission"""
        request = request_factory.get("/")
        request.user = non_dashboard_user

        permission = HasDashboardAccess()
        assert permission.has_permission(request, None) is False

    def test_unauthenticated_user(self, request_factory):
        """Test that unauthenticated user is denied permission"""
        request = request_factory.get("/")
        request.user = Mock()
        request.user.is_authenticated = False

        permission = HasDashboardAccess()
        assert permission.has_permission(request, None) is False

    def test_user_has_dashboard_access_property(self, dashboard_user):
        """Test that user.has_dashboard_access property works correctly"""
        assert dashboard_user.has_dashboard_access is True

    def test_user_without_dashboard_access_property(self, non_dashboard_user):
        """Test that user without dashboard access returns False"""
        assert non_dashboard_user.has_dashboard_access is False


@pytest.mark.django_db
class TestCanSeeConsultation:
    def test_user_with_consultation_access(
        self, request_factory, non_dashboard_user, consultation, dashboard_user
    ):
        """Test that user with access to consultation is granted permission"""
        consultation.users.add(dashboard_user)

        request = request_factory.get("/")
        request.user = non_dashboard_user

        # Mock view with consultation_slug in kwargs
        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

    def test_user_without_consultation_access(self, request_factory, dashboard_user, consultation):
        """Test that user without access to consultation is denied permission"""
        # Don't add user to consultation.users

        request = request_factory.get("/")
        request.user = dashboard_user

        view = Mock()
        view.kwargs = {"consultation_slug": consultation.slug}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_unauthenticated_user(self, request_factory, consultation):
        """Test that unauthenticated user is denied permission"""
        request = request_factory.get("/")
        request.user = Mock()
        request.user.is_authenticated = False

        view = Mock()
        view.kwargs = {"consultation_slug": consultation.slug}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_missing_consultation_slug(self, request_factory, dashboard_user):
        """Test that missing consultation_slug denies permission"""
        request = request_factory.get("/")
        request.user = dashboard_user

        # View without consultation_slug in kwargs
        view = Mock()
        view.kwargs = {}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_nonexistent_consultation_slug(self, request_factory, dashboard_user):
        """Test that nonexistent consultation slug denies permission"""
        request = request_factory.get("/")
        request.user = dashboard_user

        view = Mock()
        view.kwargs = {"consultation_slug": "nonexistent-consultation"}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_consultation_slug_as_none(self, request_factory, dashboard_user):
        """Test that None consultation_slug denies permission"""
        request = request_factory.get("/")
        request.user = dashboard_user

        view = Mock()
        view.kwargs = {"consultation_slug": None}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_multiple_users_with_access(self, request_factory, consultation):
        """Test that multiple users can have access to the same consultation"""
        user1 = UserFactory()
        user2 = UserFactory()

        # Add both users to consultation
        consultation.users.add(user1, user2)

        # Test user1
        request = request_factory.get("/")
        request.user = user1

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

        # Test user2
        request.user = user2
        assert permission.has_permission(request, view) is True

    def test_user_removed_from_consultation(self, request_factory, dashboard_user, consultation):
        """Test that user loses access when removed from consultation"""
        # Initially add user to consultation
        consultation.users.add(dashboard_user)

        request = request_factory.get("/")
        request.user = dashboard_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

        # Remove user from consultation
        consultation.users.remove(dashboard_user)

        # Should now be denied
        assert permission.has_permission(request, view) is False


@pytest.mark.django_db
class TestPermissionsCombined:
    """Test how permissions work when combined in API views"""

    def test_both_permissions_required(self, request_factory, consultation):
        """Test that both HasDashboardAccess and CanSeeConsultation must pass"""
        # User with dashboard access but not consultation access
        user_with_dashboard = UserFactory(has_dashboard_access=True)

        # User with consultation access but not dashboard access
        user_with_consultation = UserFactory()
        consultation.users.add(user_with_consultation)

        # User with both accesses
        user_with_both = UserFactory(has_dashboard_access=True)
        consultation.users.add(user_with_both)

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        dashboard_permission = HasDashboardAccess()
        consultation_permission = CanSeeConsultation()

        # Test user with only dashboard access
        request = request_factory.get("/")
        request.user = user_with_dashboard

        assert dashboard_permission.has_permission(request, view) is True
        assert consultation_permission.has_permission(request, view) is False

        # Test user with only consultation access
        request.user = user_with_consultation

        assert dashboard_permission.has_permission(request, view) is False
        assert consultation_permission.has_permission(request, view) is True

        # Test user with both accesses
        request.user = user_with_both

        assert dashboard_permission.has_permission(request, view) is True
        assert consultation_permission.has_permission(request, view) is True


@pytest.mark.django_db
class TestAPIViewPermissions:
    """Test permissions across all API views"""

    @pytest.mark.parametrize(
        "endpoint_name",
        [
            "consultations-demographic-options",
            "response-demographic-aggregations",
            "question-theme-information",
            "response-theme-aggregations",
            "response-list",
            "question-detail",
            "respondent-detail",
        ],
    )
    def test_unauthenticated_access_denied(self, client, free_text_question, endpoint_name):
        """Test that unauthenticated users cannot access any API endpoint"""
        url = build_url(endpoint_name, free_text_question)
        response = client.get(url)
        assert response.status_code == 401

    @pytest.mark.parametrize(
        "endpoint_name",
        [
            "consultations-demographic-options",
            "response-demographic-aggregations",
            "question-theme-information",
            "response-theme-aggregations",
            "response-list",
            "question-detail",
            "respondent-detail",
        ],
    )
    @pytest.mark.skip(
        reason="We want users without dashboard access to be able to do evaluations and view consultation questions"
    )
    def test_user_without_dashboard_access_denied(
        self, client, free_text_question, non_dashboard_user_token, endpoint_name
    ):
        """Test that users without dashboard access cannot access any API endpoint"""
        url = build_url(endpoint_name, free_text_question)
        response = client.get(
            url,
            headers={
                "Authorization": f"Bearer {non_dashboard_user_token}",
            },
        )
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "endpoint_name",
        [
            "consultations-detail",
            "consultations-demographic-options",
            "response-demographic-aggregations",
            "question-theme-information",
            "response-theme-aggregations",
            "response-list",
            "question-detail",
            "respondent-detail",
        ],
    )
    def test_user_without_consultation_access_denied(
        self, client, free_text_question, non_consultation_user_token, endpoint_name
    ):
        """Test that users without consultation access cannot access any API endpoint"""
        url = build_url(endpoint_name, free_text_question)
        response = client.get(
            url,
            headers={
                "Authorization": f"Bearer {non_consultation_user_token}",
            },
        )
        assert response.status_code == 403
