from unittest.mock import Mock

import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.api.permissions import (
    CanSeeConsultation,
    HasDashboardAccess,
)
from consultation_analyser.factories import ConsultationFactory, UserFactory


@pytest.fixture()
def consultation():
    return ConsultationFactory()


@pytest.fixture()
def user_with_dashboard_access():
    user = UserFactory()
    dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user.groups.add(dash_access)
    user.save()
    return user


@pytest.fixture()
def user_without_dashboard_access():
    return UserFactory()


@pytest.fixture()
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
class TestHasDashboardAccess:
    def test_authenticated_user_with_dashboard_access(self, request_factory, user_with_dashboard_access):
        """Test that authenticated user with dashboard access is granted permission"""
        request = request_factory.get('/')
        request.user = user_with_dashboard_access
        
        permission = HasDashboardAccess()
        assert permission.has_permission(request, None) is True

    def test_authenticated_user_without_dashboard_access(self, request_factory, user_without_dashboard_access):
        """Test that authenticated user without dashboard access is denied permission"""
        request = request_factory.get('/')
        request.user = user_without_dashboard_access
        
        permission = HasDashboardAccess()
        assert permission.has_permission(request, None) is False

    def test_unauthenticated_user(self, request_factory):
        """Test that unauthenticated user is denied permission"""
        request = request_factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        permission = HasDashboardAccess()
        assert permission.has_permission(request, None) is False

    def test_user_has_dashboard_access_property(self, user_with_dashboard_access):
        """Test that user.has_dashboard_access property works correctly"""
        assert user_with_dashboard_access.has_dashboard_access is True

    def test_user_without_dashboard_access_property(self, user_without_dashboard_access):
        """Test that user without dashboard access returns False"""
        assert user_without_dashboard_access.has_dashboard_access is False


@pytest.mark.django_db
class TestCanSeeConsultation:
    def test_user_with_consultation_access(self, request_factory, user_with_dashboard_access, consultation):
        """Test that user with access to consultation is granted permission"""
        consultation.users.add(user_with_dashboard_access)
        
        request = request_factory.get('/')
        request.user = user_with_dashboard_access
        
        # Mock view with consultation_slug in kwargs
        view = Mock()
        view.kwargs = {'consultation_slug': consultation.slug}
        
        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True

    def test_user_without_consultation_access(self, request_factory, user_with_dashboard_access, consultation):
        """Test that user without access to consultation is denied permission"""
        # Don't add user to consultation.users
        
        request = request_factory.get('/')
        request.user = user_with_dashboard_access
        
        view = Mock()
        view.kwargs = {'consultation_slug': consultation.slug}
        
        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_unauthenticated_user(self, request_factory, consultation):
        """Test that unauthenticated user is denied permission"""
        request = request_factory.get('/')
        request.user = Mock()
        request.user.is_authenticated = False
        
        view = Mock()
        view.kwargs = {'consultation_slug': consultation.slug}
        
        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_missing_consultation_slug(self, request_factory, user_with_dashboard_access):
        """Test that missing consultation_slug denies permission"""
        request = request_factory.get('/')
        request.user = user_with_dashboard_access
        
        # View without consultation_slug in kwargs
        view = Mock()
        view.kwargs = {}
        
        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_nonexistent_consultation_slug(self, request_factory, user_with_dashboard_access):
        """Test that nonexistent consultation slug denies permission"""
        request = request_factory.get('/')
        request.user = user_with_dashboard_access
        
        view = Mock()
        view.kwargs = {'consultation_slug': 'nonexistent-consultation'}
        
        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_consultation_slug_as_none(self, request_factory, user_with_dashboard_access):
        """Test that None consultation_slug denies permission"""
        request = request_factory.get('/')
        request.user = user_with_dashboard_access
        
        view = Mock()
        view.kwargs = {'consultation_slug': None}
        
        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is False

    def test_multiple_users_with_access(self, request_factory, consultation):
        """Test that multiple users can have access to the same consultation"""
        user1 = UserFactory()
        user2 = UserFactory()
        
        # Add both users to consultation
        consultation.users.add(user1, user2)
        
        # Test user1
        request = request_factory.get('/')
        request.user = user1
        
        view = Mock()
        view.kwargs = {'consultation_slug': consultation.slug}
        
        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True
        
        # Test user2
        request.user = user2
        assert permission.has_permission(request, view) is True

    def test_user_removed_from_consultation(self, request_factory, user_with_dashboard_access, consultation):
        """Test that user loses access when removed from consultation"""
        # Initially add user to consultation
        consultation.users.add(user_with_dashboard_access)
        
        request = request_factory.get('/')
        request.user = user_with_dashboard_access
        
        view = Mock()
        view.kwargs = {'consultation_slug': consultation.slug}
        
        permission = CanSeeConsultation()
        assert permission.has_permission(request, view) is True
        
        # Remove user from consultation
        consultation.users.remove(user_with_dashboard_access)
        
        # Should now be denied
        assert permission.has_permission(request, view) is False


@pytest.mark.django_db 
class TestPermissionsCombined:
    """Test how permissions work when combined in API views"""
    
    def test_both_permissions_required(self, request_factory, consultation):
        """Test that both HasDashboardAccess and CanSeeConsultation must pass"""
        # User with dashboard access but not consultation access
        user_with_dashboard = UserFactory()
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user_with_dashboard.groups.add(dash_access)
        user_with_dashboard.save()
        
        # User with consultation access but not dashboard access
        user_with_consultation = UserFactory()
        consultation.users.add(user_with_consultation)
        
        # User with both accesses
        user_with_both = UserFactory()
        dash_access.user_set.add(user_with_both)
        consultation.users.add(user_with_both)
        
        view = Mock()
        view.kwargs = {'consultation_slug': consultation.slug}
        
        dashboard_permission = HasDashboardAccess()
        consultation_permission = CanSeeConsultation()
        
        # Test user with only dashboard access
        request = request_factory.get('/')
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