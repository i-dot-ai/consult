from unittest.mock import patch
from uuid import uuid4

import pytest
from backend.consultations.models import Consultation, Question, SelectedTheme
from backend.factories import ConsultationFactory, RespondentFactory, UserFactory
from django.urls import reverse


@pytest.mark.django_db
class TestConsultationViewSet:
    def test_get_demographic_options_empty(
        self, client, staff_user_token, free_text_question
    ):
        """Test API endpoint returns empty options when no demographic data exists"""
        url = reverse(
            "consultations-demographic-options",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_demographic_options_with_data(
        self, client, staff_user_token, free_text_question
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
            headers={"Authorization": f"Bearer {staff_user_token}"},
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

    def test_invalid_consultation_slug(self, client, staff_user_token):
        """Test API endpoint with invalid consultation slug"""
        url = reverse("consultations-demographic-options", kwargs={"pk": uuid4()})
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 404  # NOT FOUND

    def test_consultations_list(self, client, staff_user_token, multi_choice_question):
        url = reverse("consultations-list")
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

    def test_consultations_list_filter_by_slug(
        self, client, staff_user_token, multi_choice_question
    ):
        """Test that consultations can be filtered by slug"""
        consultation = multi_choice_question.consultation

        # Test filtering by slug
        url = reverse("consultations-list")
        response = client.get(
            url,
            {"code": consultation.code},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        results = data.get("results", data)  # Handle paginated/non-paginated responses

        # Should return exactly one consultation
        assert len(results) == 1
        assert results[0]["code"] == consultation.code
        assert results[0]["title"] == consultation.title
        assert results[0]["stage"] == consultation.stage

    def test_consultations_list_filter_by_nonexistent_slug(self, client, staff_user_token):
        """Test that filtering by non-existent slug returns empty results"""

        url = reverse("consultations-list")
        response = client.get(
            url,
            {"code": "nonexistent-code"},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        results = data.get("results", data)  # Handle paginated/non-paginated responses

        # Should return empty list
        assert len(results) == 0

    def test_nonexistent_consultation(self, client, staff_user_token):
        """Test API endpoints with non-existent consultation"""
        url = reverse("consultations-demographic-options", kwargs={"pk": uuid4()})
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 404  # NOT FOUND

    def test_can_get_consultation_detail_for_consultation_users(
        self, client, consultation, staff_user_token
    ):
        """Test API endpoint grants access to users of the consultation"""
        url = reverse(
            "consultations-detail",
            kwargs={"pk": consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

    def test_can_get_consultation_detail_for_admin_users(
        self, client, consultation, staff_user_token
    ):
        """Test API endpoint grants access to admin users"""
        url = reverse(
            "consultations-detail",
            kwargs={"pk": consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

    def test_cannot_get_consultation_detail_for_unauthorized_users(
        self, client, consultation
    ):
        """Test API endpoint denies access to unauthorized users"""
        from backend.factories import UserFactory
        from rest_framework_simplejwt.tokens import RefreshToken

        # Create a user who is NOT assigned to any consultation
        isolated_user = UserFactory(is_staff=False)
        token = str(RefreshToken.for_user(isolated_user).access_token)

        url = reverse(
            "consultations-detail",
            kwargs={"pk": consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
        )
        isolated_user.delete()
        assert response.status_code == 403  # FORBIDDEN

    def test_list_all_consultations_for_admin_users(self, client, staff_user_token):
        """Test API endpoint lists all consultations for admin users"""
        ConsultationFactory.create_batch(3)

        url = reverse("consultations-list")
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert response.json()["count"] == 3

    def test_list_all_consultations_for_non_admin_users(
        self, client, non_staff_user, non_staff_user_token
    ):
        """Test API endpoint lists only assigned consultations for
        non-admin users even when scope=assigned is not specified"""
        ConsultationFactory.create_batch(3)
        assigned_consultation = ConsultationFactory.create()
        assigned_consultation.users.add(non_staff_user)

        url = reverse("consultations-list")
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_list_assigned_consultations_for_admin_users(
        self, client, staff_user, staff_user_token
    ):
        """Test API endpoint lists assigned consultations for admin users"""
        ConsultationFactory.create_batch(3)
        assigned_consultation = ConsultationFactory.create()
        assigned_consultation.users.add(staff_user)

        url = reverse("consultations-list", query={"scope": "assigned"})
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 1

    def test_list_assigned_consultations_for_non_admin_users(
        self, client, non_staff_user, non_staff_user_token
    ):
        """Test API endpoint lists assigned consultations for non-admin users"""
        ConsultationFactory.create_batch(3)
        assigned_consultation1 = ConsultationFactory.create()
        assigned_consultation1.users.add(non_staff_user)
        assigned_consultation2 = ConsultationFactory.create()
        assigned_consultation2.users.add(non_staff_user)

        url = reverse("consultations-list", query={"scope": "assigned"})
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["count"] == 2

    def test_delete_consultation(self, client, consultation, staff_user_token):
        """test that a user can delete their own consultation"""
        url = reverse("consultations-detail", kwargs={"pk": consultation.id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 204
        assert not response.content
        assert not Consultation.objects.filter(pk=consultation.pk).exists()

    def test_delete_consultation_fail(self, client, consultation, non_staff_user_token):
        """test that a user cannot delete a consultation they do not own"""
        url = reverse("consultations-detail", kwargs={"pk": consultation.id})
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )
        assert response.status_code == 403
        assert response.json()["detail"] == "You do not have permission to perform this action."
        assert Consultation.objects.filter(pk=consultation.pk).exists()

    def test_add_users_success(self, client, consultation, staff_user_token):
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
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 201
        assert response.json()["message"] == "Successfully added 2 users to consultation"
        assert consultation.users.filter(id__in=[user1.id, user2.id]).count() == 2

    def test_add_users_empty_list(self, client, consultation, staff_user_token):
        """Test adding users with empty list fails"""
        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"user_ids": []},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400
        assert "user_ids must be a non-empty list" in response.json()["error"]

    def test_add_users_nonexistent_user(self, client, consultation, staff_user_token):
        """Test adding users with non-existent user ID fails"""
        user1 = UserFactory()
        fake_id = "99999"  # Non-existent integer ID
        user_ids = [str(user1.id), fake_id]

        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"user_ids": user_ids},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 404
        assert "Only 1 of 2 users found" in response.json()["error"]

    def test_add_users_nonexistent_consultation(self, client, staff_user_token):
        """Test adding users to non-existent consultation fails"""
        user1 = UserFactory()
        fake_consultation_id = str(uuid4())

        url = reverse("consultations-add-users", kwargs={"pk": fake_consultation_id})
        response = client.post(
            url,
            {"user_ids": [str(user1.id)]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 404

    def test_add_users_permission_required(self, client, consultation, non_staff_user_token):
        """Test adding users requires proper permissions"""
        user1 = UserFactory()

        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"user_ids": [str(user1.id)]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

        assert response.status_code == 403

    def test_remove_user_success(self, client, consultation, staff_user_token):
        """Test successfully removing a user from a consultation"""
        user_to_remove = UserFactory()
        consultation.users.add(user_to_remove)

        url = reverse(
            "consultations-remove-user",
            kwargs={"pk": consultation.id, "user_id": user_to_remove.id},
        )
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert (
            f"Successfully removed user {user_to_remove.email} from consultation"
            in response.json()["message"]
        )
        assert not consultation.users.filter(id=user_to_remove.id).exists()

    def test_remove_user_not_in_consultation(self, client, consultation, staff_user_token):
        """Test removing a user who is not in the consultation fails"""
        user_not_in_consultation = UserFactory()

        url = reverse(
            "consultations-remove-user",
            kwargs={"pk": consultation.id, "user_id": user_not_in_consultation.id},
        )
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 404
        assert "User is not assigned to this consultation" in response.json()["error"]

    def test_remove_user_nonexistent_user(self, client, consultation, staff_user_token):
        """Test removing a non-existent user fails"""
        fake_user_id = "99999"

        url = reverse(
            "consultations-remove-user", kwargs={"pk": consultation.id, "user_id": fake_user_id}
        )
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["error"]

    def test_remove_user_nonexistent_consultation(self, client, staff_user_token):
        """Test removing user from non-existent consultation fails"""
        user = UserFactory()
        fake_consultation_id = str(uuid4())

        url = reverse(
            "consultations-remove-user", kwargs={"pk": fake_consultation_id, "user_id": user.id}
        )
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 404
        assert "Consultation not found" in response.json()["error"]

    def test_remove_user_invalid_user_id(self, client, consultation, staff_user_token):
        """Test removing user with invalid user ID fails"""
        invalid_user_id = "not-a-number"

        url = reverse(
            "consultations-remove-user", kwargs={"pk": consultation.id, "user_id": invalid_user_id}
        )
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400
        assert "Invalid user ID provided" in response.json()["error"]

    def test_remove_user_permission_required(
        self, client, consultation, non_staff_user_token
    ):
        """Test removing user requires proper permissions"""
        user = UserFactory()
        consultation.users.add(user)

        url = reverse(
            "consultations-remove-user", kwargs={"pk": consultation.id, "user_id": user.id}
        )
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

        assert response.status_code == 403


@pytest.mark.django_db
class TestSetupConsultationEndpoint:
    def test_setup_consultation_success(self, client, staff_user_token):
        """Test successful consultation setup"""
        url = reverse("consultations-setup")
        data = {
            "consultation_name": "Test Consultation",
            "consultation_code": "test-code",
        }

        with patch("backend.consultations.api.views.consultation.jobs") as mock_jobs:
            mock_jobs.import_consultation.delay.return_value = None

            response = client.post(
                url,
                data,
                content_type="application/json",
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 202
            assert "setup job started successfully" in response.json()["message"].lower()

            # Verify job was enqueued with correct parameters
            mock_jobs.import_consultation.delay.assert_called_once()
            call_args = mock_jobs.import_consultation.delay.call_args
            assert call_args.kwargs["consultation_code"] == "test-code"
            assert call_args.kwargs["consultation_name"] == "Test Consultation"

    def test_setup_consultation_missing_parameters(self, client, staff_user_token):
        """Test setup endpoint validates required parameters"""
        url = reverse("consultations-setup")
        data = {"consultation_name": "Test Consultation"}  # Missing consultation_code

        response = client.post(
            url,
            data,
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestGetConsultationFoldersEndpoint:
    def test_get_folders_setup_stage_with_no_consultations(self, client, staff_user_token):
        """Test setup stage returns all S3 folders when no consultations exist"""
        url = reverse("consultations-folders")

        with patch("backend.data_pipeline.s3.get_consultation_folders") as mock_get_folders:
            mock_get_folders.return_value = ["healthcare-2026", "transport-2026", "education-2026"]

            response = client.get(
                url,
                {"stage": "setup"},
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 200
            assert response.json() == ["education-2026", "healthcare-2026", "transport-2026"]

    def test_get_folders_setup_stage_excludes_existing_consultations(
        self, client, staff_user_token
    ):
        """Test setup stage excludes S3 folders that have matching consultations"""
        ConsultationFactory(code="healthcare-2026", title="Healthcare Consultation")

        url = reverse("consultations-folders")

        with patch("backend.data_pipeline.s3.get_consultation_folders") as mock_get_folders:
            mock_get_folders.return_value = ["healthcare-2026", "transport-2026", "education-2026"]

            response = client.get(
                url,
                {"stage": "setup"},
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 200
            assert response.json() == ["education-2026", "transport-2026"]

    def test_get_folders_find_themes_stage_returns_consultations(self, client, staff_user_token):
        """Test find-themes stage returns consultations with matching S3 folders"""
        # Create consultations with codes matching S3 folders
        c1 = ConsultationFactory(code="healthcare-2026", title="Healthcare Consultation")
        c2 = ConsultationFactory(code="transport-2026", title="Transport Consultation")
        # Create consultation without matching S3 folder
        ConsultationFactory(code="other-consultation", title="Other")

        url = reverse("consultations-folders")

        with patch("backend.data_pipeline.s3.get_consultation_folders") as mock_get_folders:
            mock_get_folders.return_value = ["healthcare-2026", "transport-2026", "education-2026"]

            response = client.get(
                url,
                {"stage": "find-themes"},
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 200
            result = response.json()

            assert result[0]["code"] == "healthcare-2026"
            assert result[0]["title"] == "Healthcare Consultation"
            assert result[0]["id"] == str(c1.id)

            assert result[1]["code"] == "transport-2026"
            assert result[1]["title"] == "Transport Consultation"
            assert result[1]["id"] == str(c2.id)

    def test_get_folders_assign_themes_stage_returns_consultations(self, client, staff_user_token):
        """Test assign-themes stage returns consultations with matching S3 folders"""
        c1 = ConsultationFactory(code="healthcare-2026", title="Healthcare Consultation")

        url = reverse("consultations-folders")

        with patch("backend.data_pipeline.s3.get_consultation_folders") as mock_get_folders:
            mock_get_folders.return_value = ["healthcare-2026", "education-2026"]

            response = client.get(
                url,
                {"stage": "assign-themes"},
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 200
            result = response.json()
            assert result[0]["code"] == "healthcare-2026"
            assert result[0]["id"] == str(c1.id)

    def test_get_folders_handles_one_to_many_relationship(self, client, staff_user_token):
        """Test endpoint handles multiple consultations with same code"""
        c1 = ConsultationFactory(code="healthcare-2026", title="Healthcare Consultation V1")
        c2 = ConsultationFactory(code="healthcare-2026", title="Healthcare Consultation V2")

        url = reverse("consultations-folders")

        with patch("backend.data_pipeline.s3.get_consultation_folders") as mock_get_folders:
            mock_get_folders.return_value = ["healthcare-2026"]

            response = client.get(
                url,
                {"stage": "find-themes"},
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 200
            result = response.json()

            assert result[0]["code"] == "healthcare-2026"
            assert result[0]["title"] == "Healthcare Consultation V1"
            assert result[0]["id"] == str(c1.id)

            assert result[1]["code"] == "healthcare-2026"
            assert result[1]["title"] == "Healthcare Consultation V2"
            assert result[1]["id"] == str(c2.id)

    def test_get_folders_requires_stage_parameter(self, client, staff_user_token):
        """Test endpoint validates required stage parameter"""
        url = reverse("consultations-folders")

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400

    def test_get_folders_validates_stage_choices(self, client, staff_user_token):
        """Test endpoint validates stage parameter choices"""
        url = reverse("consultations-folders")

        response = client.get(
            url,
            {"stage": "invalid-stage"},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestFindThemesEndpoint:
    def test_find_themes_success(self, client, staff_user_token, free_text_question):
        """Test successful find themes job submission"""
        consultation = free_text_question.consultation

        url = reverse("consultations-find-themes", kwargs={"pk": consultation.id})

        with patch("backend.data_pipeline.batch.submit_job") as mock_submit:
            mock_submit.return_value = {"jobId": "test-job-123"}

            response = client.post(
                url,
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 202
            assert response.json()["consultation_id"] == str(consultation.id)

            # Verify batch job was submitted
            mock_submit.assert_called_once_with(
                job_type="FIND_THEMES",
                consultation_code=consultation.code,
                consultation_name=consultation.title,
                user_id=mock_submit.call_args.kwargs["user_id"],
            )

    def test_find_themes_no_free_text_questions(self, client, staff_user_token, consultation):
        """Test find themes endpoint requires free text questions"""
        Question.objects.create(
            consultation=consultation, number=1, has_free_text=False, text="Test?"
        )

        url = reverse("consultations-find-themes", kwargs={"pk": consultation.id})

        response = client.post(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestAssignThemesEndpoint:
    def test_assign_themes_success(self, client, staff_user_token, free_text_question):
        """Test successful assign themes job submission"""
        consultation = free_text_question.consultation

        SelectedTheme.objects.create(
            question=free_text_question, name="Theme Name", description="Theme Description"
        )

        url = reverse("consultations-assign-themes", kwargs={"pk": consultation.id})

        with (
            patch(
                "backend.consultations.api.views.consultation.export_selected_themes_to_s3"
            ) as mock_export,
            patch("backend.consultations.api.views.consultation.batch") as mock_batch,
        ):
            mock_export.return_value = 1
            mock_batch.submit_job.return_value = {"jobId": "test-job-456"}

            response = client.post(
                url,
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 202

            # Verify seletected themes were exported to S3
            mock_export.assert_called_once_with(consultation)

            # Verify batch job was submitted
            mock_batch.submit_job.assert_called_once_with(
                job_type="ASSIGN_THEMES",
                consultation_code=consultation.code,
                consultation_name=consultation.title,
                user_id=mock_batch.submit_job.call_args.kwargs["user_id"],
            )

    def test_assign_themes_no_selected_themes(self, client, staff_user_token, free_text_question):
        """Test assign themes fails when no themes are selected"""
        consultation = free_text_question.consultation

        url = reverse("consultations-assign-themes", kwargs={"pk": consultation.id})

        with patch(
            "backend.consultations.api.views.consultation.export_selected_themes_to_s3"
        ) as mock_export:
            mock_export.side_effect = ValueError("No questions with selected themes found")

            response = client.post(
                url,
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 400
