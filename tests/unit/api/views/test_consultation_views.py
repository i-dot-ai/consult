from uuid import uuid4

import pytest
from django.urls import reverse

from consultation_analyser.consultations.models import Consultation
from consultation_analyser.factories import ConsultationFactory, RespondentFactory, UserFactory


@pytest.mark.django_db
class TestConsultationViewSet:
    def test_get_demographic_options_empty(
        self, client, consultation_user_token, free_text_question
    ):
        """Test API endpoint returns empty options when no demographic data exists"""
        url = reverse(
            "consultations-demographic-options",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_demographic_options_with_data(
        self, client, consultation_user_token, free_text_question
    ):
        """Test API endpoint returns demographic options correctly"""
        # Create respondents with different demographic data
        RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": True, "region": "north", "age": 25},
        )
        RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": False, "region": "south", "age": 35},
        )
        RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": True, "region": "north", "age": 45},
        )

        url = reverse(
            "consultations-demographic-options",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        expected = [
            {"count": 1, "name": "age", "value": "25"},
            {"count": 1, "name": "age", "value": "35"},
            {"count": 1, "name": "age", "value": "45"},
            {"count": 1, "name": "individual", "value": False},
            {"count": 2, "name": "individual", "value": True},
            {"count": 2, "name": "region", "value": "north"},
            {"count": 1, "name": "region", "value": "south"},
        ]

        def f(x):
            return {k: v for k, v in x.items() if k != "id"}

        def _sort(items):
            return sorted(items, key=lambda x: (x["name"], x["value"]))

        assert _sort(map(f, data)) == _sort(expected)

    def test_permission_required(self, client, free_text_question):
        """Test API endpoint requires proper permissions"""
        url = reverse(
            "consultations-demographic-options",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(url)
        assert response.status_code == 401

    def test_invalid_consultation_slug(self, client, consultation_user_token):
        """Test API endpoint with invalid consultation slug"""
        url = reverse("consultations-demographic-options", kwargs={"pk": uuid4()})
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 404  # NOT FOUND

    def test_consultations_list(self, client, consultation_user_token, multi_choice_question):
        url = reverse("consultations-list")
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 200

    def test_consultations_list_filter_by_slug(
        self, client, consultation_user_token, multi_choice_question
    ):
        """Test that consultations can be filtered by slug"""
        consultation = multi_choice_question.consultation

        # Test filtering by slug
        url = reverse("consultations-list")
        response = client.get(
            url,
            {"code": consultation.code},
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        results = data.get("results", data)  # Handle paginated/non-paginated responses

        # Should return exactly one consultation
        assert len(results) == 1
        assert results[0]["code"] == consultation.code
        assert results[0]["title"] == consultation.title
        assert results[0]["stage"] == consultation.stage

    def test_consultations_list_filter_by_nonexistent_slug(self, client, consultation_user_token):
        """Test that filtering by non-existent slug returns empty results"""

        url = reverse("consultations-list")
        response = client.get(
            url,
            {"code": "nonexistent-code"},
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        results = data.get("results", data)  # Handle paginated/non-paginated responses

        # Should return empty list
        assert len(results) == 0

    def test_nonexistent_consultation(self, client, consultation_user_token):
        """Test API endpoints with non-existent consultation"""
        url = reverse("consultations-demographic-options", kwargs={"pk": uuid4()})
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 404  # NOT FOUND

    def test_can_get_consultation_detail_for_consultation_users(
        self, client, consultation, consultation_user_token
    ):
        """Test API endpoint grants access to users of the consultation"""
        url = reverse(
            "consultations-detail",
            kwargs={"pk": consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 200

    def test_can_get_consultation_detail_for_admin_users(
        self, client, consultation, admin_user_token
    ):
        """Test API endpoint grants access to admin users"""
        url = reverse(
            "consultations-detail",
            kwargs={"pk": consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        assert response.status_code == 200

    def test_cannot_get_consultation_detail_for_unauthorized_users(
        self, client, consultation, non_consultation_user_token
    ):
        """Test API endpoint denies access to unauthorized users"""
        url = reverse(
            "consultations-detail",
            kwargs={"pk": consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {non_consultation_user_token}"},
        )
        assert response.status_code == 403  # FORBIDDEN

    def test_list_all_consultations_for_admin_users(self, client, admin_user_token):
        """Test API endpoint lists all consultations for admin users"""
        ConsultationFactory.create_batch(3)

        url = reverse("consultations-list")
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )

        assert response.status_code == 200
        assert response.json()["count"] == 3

    def test_list_all_consultations_for_non_admin_users(
        self, client, dashboard_user, dashboard_user_token
    ):
        """Test API endpoint lists only assigned consultations for
        non-admin users even when scope=assigned is not specified"""
        ConsultationFactory.create_batch(3)
        assigned_consultation = ConsultationFactory.create()
        assigned_consultation.users.add(dashboard_user)

        url = reverse("consultations-list")
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {dashboard_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_list_assigned_consultations_for_admin_users(
        self, client, admin_user, admin_user_token
    ):
        """Test API endpoint lists assigned consultations for admin users"""
        ConsultationFactory.create_batch(3)
        assigned_consultation = ConsultationFactory.create()
        assigned_consultation.users.add(admin_user)

        url = reverse("consultations-list", query={"scope": "assigned"})
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {admin_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_list_assigned_consultations_for_non_admin_users(
        self, client, dashboard_user, dashboard_user_token
    ):
        """Test API endpoint lists assigned consultations for non-admin users"""
        ConsultationFactory.create_batch(3)
        assigned_consultation1 = ConsultationFactory.create()
        assigned_consultation1.users.add(dashboard_user)
        assigned_consultation2 = ConsultationFactory.create()
        assigned_consultation2.users.add(dashboard_user)

        url = reverse("consultations-list", query={"scope": "assigned"})
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {dashboard_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_delete_consultation(self, client, consultation, consultation_user_token):
        """test that a user can delete their own consultation"""
        url = reverse("consultations-detail", kwargs={"pk": consultation.id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 204
        assert not response.content
        assert not Consultation.objects.filter(pk=consultation.pk).exists()

    def test_delete_consultation_fail(self, client, consultation, non_consultation_user_token):
        """test that a user cannot delete a consultation they do not own"""
        url = reverse("consultations-detail", kwargs={"pk": consultation.id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {non_consultation_user_token}"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have permission to perform this action."
        assert Consultation.objects.filter(pk=consultation.pk).exists()

    def test_add_users_success(self, client, consultation, consultation_user_token):
        """Test successfully adding multiple users to a consultation"""
        # Create test users
        user1 = UserFactory()
        user2 = UserFactory()
        user_ids = [str(user1.id), str(user2.id)]

        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"user_ids": user_ids},
            content_type="application/json",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 201
        assert response.json()["message"] == "Successfully added 2 users to consultation"
        assert consultation.users.filter(id__in=[user1.id, user2.id]).count() == 2

    def test_add_users_empty_list(self, client, consultation, consultation_user_token):
        """Test adding users with empty list fails"""
        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"user_ids": []},
            content_type="application/json",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 400
        assert "user_ids must be a non-empty list" in response.json()["error"]

    def test_add_users_nonexistent_user(self, client, consultation, consultation_user_token):
        """Test adding users with non-existent user ID fails"""
        user1 = UserFactory()
        fake_id = "99999"  # Non-existent integer ID
        user_ids = [str(user1.id), fake_id]

        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"user_ids": user_ids},
            content_type="application/json",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 404
        assert "Only 1 of 2 users found" in response.json()["error"]

    def test_add_users_nonexistent_consultation(self, client, consultation_user_token):
        """Test adding users to non-existent consultation fails"""
        user1 = UserFactory()
        fake_consultation_id = str(uuid4())

        url = reverse("consultations-add-users", kwargs={"pk": fake_consultation_id})
        response = client.post(
            url,
            {"user_ids": [str(user1.id)]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 404

    def test_add_users_permission_required(self, client, consultation, non_consultation_user_token):
        """Test adding users requires proper permissions"""
        user1 = UserFactory()

        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"user_ids": [str(user1.id)]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {non_consultation_user_token}"},
        )

        assert response.status_code == 403

    def test_remove_user_success(self, client, consultation, consultation_user_token):
        """Test successfully removing a user from a consultation"""
        user_to_remove = UserFactory()
        consultation.users.add(user_to_remove)
        
        url = reverse("consultations-remove-user", kwargs={"pk": consultation.id, "user_id": user_to_remove.id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        
        assert response.status_code == 200
        assert f"Successfully removed user {user_to_remove.email} from consultation" in response.json()["message"]
        assert not consultation.users.filter(id=user_to_remove.id).exists()

    def test_remove_user_not_in_consultation(self, client, consultation, consultation_user_token):
        """Test removing a user who is not in the consultation fails"""
        user_not_in_consultation = UserFactory()
        
        url = reverse("consultations-remove-user", kwargs={"pk": consultation.id, "user_id": user_not_in_consultation.id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        
        assert response.status_code == 404
        assert "User is not assigned to this consultation" in response.json()["error"]

    def test_remove_user_nonexistent_user(self, client, consultation, consultation_user_token):
        """Test removing a non-existent user fails"""
        fake_user_id = "99999"
        
        url = reverse("consultations-remove-user", kwargs={"pk": consultation.id, "user_id": fake_user_id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["error"]

    def test_remove_user_nonexistent_consultation(self, client, consultation_user_token):
        """Test removing user from non-existent consultation fails"""
        user = UserFactory()
        fake_consultation_id = str(uuid4())
        
        url = reverse("consultations-remove-user", kwargs={"pk": fake_consultation_id, "user_id": user.id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        
        assert response.status_code == 404
        assert "Consultation not found" in response.json()["error"]

    def test_remove_user_invalid_user_id(self, client, consultation, consultation_user_token):
        """Test removing user with invalid user ID fails"""
        invalid_user_id = "not-a-number"
        
        url = reverse("consultations-remove-user", kwargs={"pk": consultation.id, "user_id": invalid_user_id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        
        assert response.status_code == 400
        assert "Invalid user ID provided" in response.json()["error"]

    def test_remove_user_permission_required(self, client, consultation, non_consultation_user_token):
        """Test removing user requires proper permissions"""
        user = UserFactory()
        consultation.users.add(user)
        
        url = reverse("consultations-remove-user", kwargs={"pk": consultation.id, "user_id": user.id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {non_consultation_user_token}"},
        )
        
        assert response.status_code == 403
