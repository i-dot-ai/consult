from unittest.mock import Mock
from uuid import uuid4

import pytest
from backend.consultations.api.permissions import (
    CanSeeConsultation,
)
from backend.factories import UserFactory

from tests.utils import build_url


@pytest.mark.django_db
class TestCanSeeConsultation:
    def test_user_with_consultation_access(
        self, request_factory, non_dashboard_user, consultation, dashboard_user
    ):
        """Test that user with access to consultation is granted permission"""
        request = request_factory.get("/")
        request.user = non_dashboard_user

        # Mock view with consultation_slug in kwargs
        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

    def test_user_without_consultation_access(
        self, request_factory, user_without_consultation_access, consultation
    ):
        """Test that user without access to consultation is denied permission"""
        request = request_factory.get("/")
        request.user = user_without_consultation_access

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_unauthenticated_user(self, request_factory, consultation):
        """Test that unauthenticated user is denied permission"""
        request = request_factory.get("/")
        request.user = Mock()
        request.user.is_authenticated = False

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_missing_consultation_pk(self, request_factory, dashboard_user):
        """Test that missing consultation_pk grants permission"""
        request = request_factory.get("/")
        request.user = dashboard_user

        view = Mock()
        view.kwargs = {}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

    def test_nonexistent_consultation_pk(self, request_factory, dashboard_user):
        """Test that nonexistent consultation_pk denies permission"""
        request = request_factory.get("/")
        request.user = dashboard_user

        view = Mock()
        view.kwargs = {"consultation_pk": uuid4()}

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

    def test_consultation_pk_preference(self, request_factory, dashboard_user, consultation):
        """Test that consultation_pk is preferred over pk in kwargs for nested routes"""
        request = request_factory.get("/")
        request.user = dashboard_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id, "pk": "some-other-id"}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

    def test_uses_pk_when_consultation_pk_not_provided(
        self, request_factory, dashboard_user, consultation
    ):
        """Test that pk is used when consultation_pk is not provided"""
        request = request_factory.get("/")
        request.user = dashboard_user

        view = Mock()
        view.kwargs = {"pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True


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
