from unittest.mock import Mock
from uuid import uuid4

import pytest

from consultations.api.permissions import (
    CanSeeConsultation,
)
from consultations.api.views_v2.permissions import (
    CanSeeConsultationV2,
    IsConsultationOwnerOrSuperuser,
)
from factories import ConsultationFactory, UserFactory
from tests.utils import build_url


@pytest.mark.django_db
class TestCanSeeConsultation:
    def test_user_with_consultation_access(
        self, request_factory, non_staff_user, consultation, staff_user
    ):
        """Test that user with access to consultation is granted permission"""
        request = request_factory.get("/")
        request.user = non_staff_user

        # Mock view with consultation_slug in kwargs
        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

    def test_user_without_consultation_access(self, request_factory, non_staff_user, consultation):
        """Test that user without access to consultation is denied permission"""
        # Remove the user from consultation to test denial
        consultation.users.remove(non_staff_user)

        request = request_factory.get("/")
        request.user = non_staff_user

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

    def test_missing_consultation_pk(self, request_factory, non_staff_user):
        """Test that missing consultation_pk grants permission"""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

    def test_nonexistent_consultation_pk(self, request_factory, non_staff_user):
        """Test that nonexistent consultation_pk denies permission"""
        request = request_factory.get("/")
        request.user = non_staff_user

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

    def test_user_removed_from_consultation(self, request_factory, non_staff_user, consultation):
        """Test that user loses access when removed from consultation"""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

        # Remove user from consultation
        consultation.users.remove(non_staff_user)

        # Should now be denied
        assert permission.has_permission(request, view) is False

    def test_consultation_pk_preference(self, request_factory, non_staff_user, consultation):
        """Test that consultation_pk is preferred over pk in kwargs for nested routes"""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id, "pk": "some-other-id"}

        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

    def test_uses_pk_when_consultation_pk_not_provided(
        self, request_factory, non_staff_user, consultation
    ):
        """Test that pk is used when consultation_pk is not provided"""
        request = request_factory.get("/")
        request.user = non_staff_user

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
            "consultations-demographics",
            "question-themes",
            "response-list",
            "question-detail",
            "question-response-list",
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
            "consultations-demographics",
            "question-themes",
            "response-list",
            "question-detail",
            "question-response-list",
            "respondent-detail",
        ],
    )
    @pytest.mark.skip(
        reason="We want users without dashboard access to be able to do evaluations and view consultation questions"
    )
    def test_user_without_dashboard_access_denied(
        self, client, free_text_question, non_staff_user_token, endpoint_name
    ):
        """Test that users without dashboard access cannot access any API endpoint"""
        url = build_url(endpoint_name, free_text_question)
        response = client.get(
            url,
            headers={
                "Authorization": f"Bearer {non_staff_user_token}",
            },
        )
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "endpoint_name",
        [
            "consultations-detail",
            "consultations-demographics",
            "question-themes",
            "response-list",
            "question-detail",
            "question-response-list",
            "respondent-detail",
        ],
    )
    def test_user_without_consultation_access_denied(
        self, client, free_text_question, endpoint_name
    ):
        """Test that users without consultation access cannot access any API endpoint"""
        from rest_framework_simplejwt.tokens import RefreshToken

        from factories import UserFactory

        # Create a user who is NOT assigned to any consultation
        isolated_user = UserFactory(is_staff=False)
        token = str(RefreshToken.for_user(isolated_user).access_token)

        url = build_url(endpoint_name, free_text_question)
        response = client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )
        isolated_user.delete()
        assert response.status_code == 403


@pytest.mark.django_db
class TestCanSeeConsultationV2:
    def test_assigned_user_can_see_consultation(self, request_factory, non_staff_user, consultation):
        """A user in the users M2M is granted access."""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert CanSeeConsultationV2().has_permission(request, view) is True

    def test_owner_can_see_consultation(self, request_factory, non_staff_user):
        """A user set as created_by is granted access even if not in users M2M."""
        consultation = ConsultationFactory(created_by=non_staff_user)

        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert CanSeeConsultationV2().has_permission(request, view) is True

    def test_unrelated_user_denied(self, request_factory, consultation):
        """A user with no relationship to the consultation is denied."""
        other_user = UserFactory()

        request = request_factory.get("/")
        request.user = other_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert CanSeeConsultationV2().has_permission(request, view) is False

    def test_superuser_can_see_any_consultation(self, request_factory, consultation):
        """A staff user bypasses the consultation check entirely."""
        superuser = UserFactory(is_staff=True)

        request = request_factory.get("/")
        request.user = superuser

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert CanSeeConsultationV2().has_permission(request, view) is True

    def test_staff_but_not_superuser_is_not_bypassed(self, request_factory, consultation):
        """A non-staff user with no relationship to the consultation is denied."""
        non_staff_user = UserFactory(is_staff=False)

        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert CanSeeConsultationV2().has_permission(request, view) is False

    def test_unauthenticated_user_denied(self, request_factory, consultation):
        """Unauthenticated requests are always denied."""
        request = request_factory.get("/")
        request.user = Mock()
        request.user.is_authenticated = False

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert CanSeeConsultationV2().has_permission(request, view) is False

    def test_missing_consultation_pk_grants_access(self, request_factory, non_staff_user):
        """No consultation pk in kwargs means no restriction — allow through."""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {}

        assert CanSeeConsultationV2().has_permission(request, view) is True

    def test_nonexistent_consultation_pk_denied(self, request_factory, non_staff_user):
        """A pk that matches no consultation is denied."""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": uuid4()}

        assert CanSeeConsultationV2().has_permission(request, view) is False

    def test_consultation_pk_preferred_over_pk(self, request_factory, non_staff_user, consultation):
        """consultation_pk takes precedence over pk in kwargs."""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id, "pk": uuid4()}

        assert CanSeeConsultationV2().has_permission(request, view) is True


@pytest.mark.django_db
class TestIsConsultationOwnerOrSuperuser:
    def test_owner_is_granted_access(self, request_factory, non_staff_user):
        """The user recorded as created_by is granted access."""
        consultation = ConsultationFactory(created_by=non_staff_user)

        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert IsConsultationOwnerOrSuperuser().has_permission(request, view) is True

    def test_assigned_user_who_is_not_owner_is_denied(self, request_factory, non_staff_user, consultation):
        """A user in the users M2M but not the owner is denied."""
        # non_staff_user is in consultation.users but is not created_by
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert IsConsultationOwnerOrSuperuser().has_permission(request, view) is False

    def test_superuser_is_granted_access(self, request_factory, consultation):
        """A staff user bypasses the ownership check entirely."""
        superuser = UserFactory(is_staff=True)

        request = request_factory.get("/")
        request.user = superuser

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert IsConsultationOwnerOrSuperuser().has_permission(request, view) is True

    def test_staff_but_not_superuser_is_denied(self, request_factory, consultation):
        """A non-staff user with no ownership is denied."""
        non_staff_user = UserFactory(is_staff=False)

        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert IsConsultationOwnerOrSuperuser().has_permission(request, view) is False

    def test_unauthenticated_user_denied(self, request_factory, consultation):
        """Unauthenticated requests are always denied."""
        request = request_factory.get("/")
        request.user = Mock()
        request.user.is_authenticated = False

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert IsConsultationOwnerOrSuperuser().has_permission(request, view) is False

    def test_missing_consultation_pk_denied(self, request_factory, non_staff_user):
        """No consultation pk means we cannot verify ownership — deny."""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {}

        assert IsConsultationOwnerOrSuperuser().has_permission(request, view) is False

    def test_nonexistent_consultation_pk_denied(self, request_factory, non_staff_user):
        """A pk that matches no consultation is denied."""
        request = request_factory.get("/")
        request.user = non_staff_user

        view = Mock()
        view.kwargs = {"consultation_pk": uuid4()}

        assert IsConsultationOwnerOrSuperuser().has_permission(request, view) is False

    def test_unrelated_user_denied(self, request_factory, consultation):
        """A user with no relationship to the consultation is denied."""
        other_user = UserFactory()

        request = request_factory.get("/")
        request.user = other_user

        view = Mock()
        view.kwargs = {"consultation_pk": consultation.id}

        assert IsConsultationOwnerOrSuperuser().has_permission(request, view) is False
