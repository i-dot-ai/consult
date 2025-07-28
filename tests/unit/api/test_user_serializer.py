import pytest
from django.contrib.auth.models import Group

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.api.serializers import UserSerializer
from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
class TestUserSerializer:
    """Test the UserSerializer in isolation"""

    def test_serializer_basic_user(self):
        """Test serializer with a basic user"""
        user = UserFactory(email="basic@example.com", is_staff=False)

        serializer = UserSerializer(user)
        data = serializer.data

        assert data["id"] == user.id
        assert data["email"] == "basic@example.com"
        assert data["is_staff"] is False
        assert data["has_dashboard_access"] is False

    def test_serializer_staff_user(self):
        """Test serializer with a staff user"""
        user = UserFactory(email="staff@example.com", is_staff=True)

        serializer = UserSerializer(user)
        data = serializer.data

        assert data["id"] == user.id
        assert data["email"] == "staff@example.com"
        assert data["is_staff"] is True
        assert data["has_dashboard_access"] is False

    def test_serializer_user_with_dashboard_access(self):
        """Test serializer with user who has dashboard access"""
        user = UserFactory(email="dashboard@example.com")
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        serializer = UserSerializer(user)
        data = serializer.data

        assert data["id"] == user.id
        assert data["email"] == "dashboard@example.com"
        assert data["is_staff"] is False
        assert data["has_dashboard_access"] is True

    def test_serializer_staff_with_dashboard_access(self):
        """Test serializer with staff user who has dashboard access"""
        user = UserFactory(email="admin@example.com", is_staff=True)
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        serializer = UserSerializer(user)
        data = serializer.data

        assert data["id"] == user.id
        assert data["email"] == "admin@example.com"
        assert data["is_staff"] is True
        assert data["has_dashboard_access"] is True


    def test_serializer_has_dashboard_access_readonly(self):
        """Test that has_dashboard_access is properly computed as readonly"""
        user = UserFactory(email="readonly@example.com")

        # Initially no dashboard access
        serializer = UserSerializer(user)
        data = serializer.data
        assert data["has_dashboard_access"] is False

        # Add dashboard access
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        # Should reflect the change
        serializer = UserSerializer(user)
        data = serializer.data
        assert data["has_dashboard_access"] is True

    def test_serializer_with_inactive_user(self):
        """Test serializer with inactive user"""
        user = UserFactory(email="inactive@example.com", is_active=False)

        serializer = UserSerializer(user)
        data = serializer.data

        assert data["email"] == "inactive@example.com"
        # Note: is_active is not included in the serializer fields
        # This is intentional as the frontend doesn't need this info
        assert "is_active" not in data

    def test_serializer_email_with_special_characters(self):
        """Test serializer handles emails with special characters"""
        user = UserFactory(email="test+tag@sub-domain.example.co.uk")

        serializer = UserSerializer(user)
        data = serializer.data

        assert data["email"] == "test+tag@sub-domain.example.co.uk"

    def test_serializer_consistent_data_types(self):
        """Test that serializer returns consistent data types"""
        user = UserFactory(email="types@example.com", is_staff=True)
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        serializer = UserSerializer(user)
        data = serializer.data

        # Verify data types
        assert isinstance(data["id"], int)
        assert isinstance(data["email"], str)
        assert isinstance(data["is_staff"], bool)
        assert isinstance(data["has_dashboard_access"], bool)

    def test_serializer_multiple_groups(self):
        """Test that has_dashboard_access works correctly when user has multiple groups"""
        user = UserFactory(email="multigroup@example.com")

        # Create additional group (not dashboard access)
        other_group = Group.objects.create(name="Other Group")
        user.groups.add(other_group)
        user.save()

        serializer = UserSerializer(user)
        data = serializer.data
        assert data["has_dashboard_access"] is False

        # Now add dashboard access group
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()

        serializer = UserSerializer(user)
        data = serializer.data
        assert data["has_dashboard_access"] is True

    def test_serializer_empty_groups(self):
        """Test serializer with user who has no groups"""
        user = UserFactory(email="nogroups@example.com")
        # Ensure user has no groups
        user.groups.clear()

        serializer = UserSerializer(user)
        data = serializer.data

        assert data["has_dashboard_access"] is False

    def test_serializer_metadata(self):
        """Test serializer metadata and model configuration"""
        serializer = UserSerializer()

        # Check Meta configuration
        assert hasattr(serializer.Meta, "model")
        assert hasattr(serializer.Meta, "fields")

        # Verify expected fields are configured
        expected_fields = ["id", "email", "is_staff", "has_dashboard_access"]
        assert serializer.Meta.fields == expected_fields

    def test_serializer_multiple_instances(self):
        """Test serializer with multiple user instances (many=True)"""
        user1 = UserFactory(email="user1@example.com", is_staff=True)
        user2 = UserFactory(email="user2@example.com", is_staff=False)

        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user2.groups.add(dash_access)
        user2.save()

        users = [user1, user2]
        serializer = UserSerializer(users, many=True)
        data = serializer.data

        assert len(data) == 2

        # Verify first user
        assert data[0]["email"] == "user1@example.com"
        assert data[0]["is_staff"] is True
        assert data[0]["has_dashboard_access"] is False

        # Verify second user
        assert data[1]["email"] == "user2@example.com"
        assert data[1]["is_staff"] is False
        assert data[1]["has_dashboard_access"] is True
