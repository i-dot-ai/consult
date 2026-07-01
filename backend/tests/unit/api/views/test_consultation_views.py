from unittest.mock import patch
from uuid import uuid4

import pytest
from django.urls import reverse

from consultations.models import (
    Consultation,
    DemographicOption,
    Question,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    ResponseReadBy,
    SelectedTheme,
)
from factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
    SelectedThemeFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestConsultationViewSet:
    def test_get_demographic_options_empty(self, client, staff_user_token, free_text_question):
        """Test API endpoint returns empty options when no demographic data exists"""
        url = reverse(
            "consultations-demographics",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_demographic_options_with_data(self, client, staff_user_token, free_text_question):
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
            "consultations-demographics",
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

    def test_get_demographics_scoped_to_question(
        self, client, staff_user_token, consultation, free_text_question
    ):
        """Test demographics endpoint scopes counts to a specific question when question_id is provided"""
        # Create two questions with different respondents
        question_2 = QuestionFactory(consultation=consultation, has_free_text=True, number=3)

        demo = DemographicOption.objects.create(
            consultation=consultation, field_name="region", field_value="north"
        )

        # Respondent 1 answers free_text_question only
        respondent1 = RespondentFactory(consultation=consultation)
        respondent1.demographics.add(demo)
        ResponseFactory(question=free_text_question, respondent=respondent1)

        # Respondent 2 answers question_2 only
        respondent2 = RespondentFactory(consultation=consultation)
        respondent2.demographics.add(demo)
        ResponseFactory(question=question_2, respondent=respondent2)

        # Update denormalised counts
        DemographicOption.update_response_counts(consultation)

        url = reverse("consultations-demographics", kwargs={"pk": consultation.id})

        # Without question_id — should count both respondents
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        counts = {
            item["value"]: item["count"] for item in response.json() if item["name"] == "region"
        }
        assert counts["north"] == 2

        # With question_id — should count only respondent1
        response = client.get(
            url,
            query_params={"question_id": free_text_question.id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        counts = {
            item["value"]: item["count"] for item in response.json() if item["name"] == "region"
        }
        assert counts["north"] == 1

    def test_get_demographics_with_theme_filter(
        self, client, staff_user_token, free_text_question, theme_a
    ):
        """Test demographics endpoint filters counts when themeFilters is applied"""
        demo = DemographicOption.objects.create(
            consultation=free_text_question.consultation,
            field_name="individual",
            field_value=True,
        )

        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent1.demographics.add(demo)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2.demographics.add(demo)

        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        ResponseFactory(question=free_text_question, respondent=respondent2)

        # Only assign theme_a to response1
        annotation = ResponseAnnotation.objects.create(response=response1)
        ResponseAnnotationTheme.objects.create(response_annotation=annotation, theme=theme_a)

        url = reverse(
            "consultations-demographics",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            query_params={"themeFilters": str(theme_a.id)},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        counts = {item["value"]: item["count"] for item in response.json()}
        assert counts[True] == 1

    def test_permission_required(self, client, free_text_question):
        """Test API endpoint requires proper permissions"""
        url = reverse(
            "consultations-demographics",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(url)
        assert response.status_code == 401

    def test_invalid_consultation_slug(self, client, staff_user_token):
        """Test API endpoint with invalid consultation slug"""
        url = reverse("consultations-demographics", kwargs={"pk": uuid4()})
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
        url = reverse("consultations-demographics", kwargs={"pk": uuid4()})
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

    def test_cannot_get_consultation_detail_for_unauthorized_users(self, client, consultation):
        """Test API endpoint denies access to unauthorized users"""
        from rest_framework_simplejwt.tokens import RefreshToken

        from factories import UserFactory

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
        from unittest.mock import patch

        url = reverse("consultations-detail", kwargs={"pk": consultation.id})

        # Mock the job enqueueing
        with patch("ingest.jobs.delete_consultation_job.delay") as mock_delay:
            response = client.delete(
                url,
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            # Verify API returned 202 Accepted
            assert response.status_code == 202

            # Verify response contains expected message
            response_data = response.json()
            assert "message" in response_data
            assert "queued" in response_data["message"]
            assert "consultation_id" in response_data

            # Verify job was enqueued with correct parameter
            mock_delay.assert_called_once_with(consultation.id)

        # Consultation should still exist (worker will delete it)
        assert Consultation.objects.filter(pk=consultation.pk).exists()

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
        user1 = UserFactory(email="user1@test.com")
        user2 = UserFactory(email="user2@test.com")
        emails = [user1.email, user2.email]

        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"emails": emails},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["message"] == "Added 2 users to consultation"
        assert response_data["added_count"] == 2
        assert response_data["non_existent_emails"] == []
        assert response_data["total_requested"] == 2
        assert consultation.users.filter(id__in=[user1.id, user2.id]).count() == 2

    def test_add_users_empty_list(self, client, consultation, staff_user_token):
        """Test adding users with empty list fails"""
        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"emails": []},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400
        assert "emails must be a non-empty list" in response.json()["error"]

    def test_add_users_nonexistent_user(self, client, consultation, staff_user_token):
        """Test adding users with non-existent email addresses"""
        user1 = UserFactory(email="existing@test.com")
        fake_email = "nonexistent@test.com"
        emails = [user1.email, fake_email]

        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"emails": emails},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 201
        response_data = response.json()
        assert response_data["message"] == "Added 1 users to consultation"
        assert response_data["added_count"] == 1
        assert response_data["non_existent_emails"] == [fake_email]
        assert response_data["total_requested"] == 2
        assert consultation.users.filter(id=user1.id).exists()

    def test_add_users_nonexistent_consultation(self, client, staff_user_token):
        """Test adding users to non-existent consultation fails"""
        user1 = UserFactory(email="test@example.com")
        fake_consultation_id = str(uuid4())

        url = reverse("consultations-add-users", kwargs={"pk": fake_consultation_id})
        response = client.post(
            url,
            {"emails": [user1.email]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 404

    def test_add_users_permission_required(self, client, consultation, non_staff_user_token):
        """Test adding users requires proper permissions"""
        user1 = UserFactory(email="test@example.com")

        url = reverse("consultations-add-users", kwargs={"pk": consultation.id})
        response = client.post(
            url,
            {"emails": [user1.email]},
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

    def test_remove_user_permission_required(self, client, consultation, non_staff_user_token):
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

        with patch("consultations.api.views.consultation.jobs") as mock_jobs:
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

        with patch("data_pipeline.s3.get_consultation_folders") as mock_get_folders:
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

        with patch("data_pipeline.s3.get_consultation_folders") as mock_get_folders:
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
        c1 = ConsultationFactory(
            code="healthcare-2026", title="Healthcare Consultation", stage=Consultation.Stage.SETUP
        )
        c2 = ConsultationFactory(
            code="transport-2026", title="Transport Consultation", stage=Consultation.Stage.SETUP
        )
        # Create consultation without matching S3 folder
        ConsultationFactory(
            code="other-consultation", title="Other", stage=Consultation.Stage.SETUP
        )

        url = reverse("consultations-folders")

        with patch("data_pipeline.s3.get_consultation_folders") as mock_get_folders:
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

    def test_get_folders_find_themes_stage_excludes_non_setup_consultations(
        self, client, staff_user_token
    ):
        """Test find-themes stage excludes consultations not in SETUP stage"""
        # Matching S3 folder, but not in SETUP stage - should be excluded
        ConsultationFactory(
            code="healthcare-2026",
            title="Healthcare Consultation",
            stage=Consultation.Stage.FINDING_THEMES,
        )

        url = reverse("consultations-folders")

        with patch("data_pipeline.s3.get_consultation_folders") as mock_get_folders:
            mock_get_folders.return_value = ["healthcare-2026", "education-2026"]

            response = client.get(
                url,
                {"stage": "find-themes"},
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 200
            assert response.json() == []

    def test_get_folders_handles_one_to_many_relationship(self, client, staff_user_token):
        """Test endpoint handles multiple consultations with same code"""
        c1 = ConsultationFactory(
            code="healthcare-2026",
            title="Healthcare Consultation V1",
            stage=Consultation.Stage.SETUP,
        )
        c2 = ConsultationFactory(
            code="healthcare-2026",
            title="Healthcare Consultation V2",
            stage=Consultation.Stage.SETUP,
        )

        url = reverse("consultations-folders")

        with patch("data_pipeline.s3.get_consultation_folders") as mock_get_folders:
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

        with patch("data_pipeline.batch.submit_job") as mock_submit:
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
                model_name=consultation.model_name,
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

    def test_find_themes_rejects_wrong_stage(self, client, staff_user_token, free_text_question):
        """Test find themes endpoint rejects consultations not in setup stage"""
        consultation = free_text_question.consultation
        consultation.stage = Consultation.Stage.FINDING_THEMES
        consultation.save(update_fields=["stage"])

        url = reverse("consultations-find-themes", kwargs={"pk": consultation.id})

        response = client.post(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400


@pytest.mark.django_db
class TestAssignThemesEndpoint:
    def test_assign_themes_success(self, client, staff_user_token, free_text_question):
        """Test assign themes exports selected themes and advances stage from finalising"""
        consultation = free_text_question.consultation
        consultation.stage = Consultation.Stage.FINALISING_THEMES
        consultation.save(update_fields=["stage"])

        SelectedTheme.objects.create(
            question=free_text_question, name="Theme Name", description="Theme Description"
        )

        url = reverse("consultations-assign-themes", kwargs={"pk": consultation.id})

        with (
            patch(
                "consultations.api.views.consultation.export_selected_themes_to_s3"
            ) as mock_export,
            patch("consultations.api.views.consultation.batch") as mock_batch,
        ):
            mock_export.return_value = 1
            mock_batch.submit_job.return_value = {"jobId": "test-job-789"}

            response = client.post(
                url,
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

            assert response.status_code == 202

            # Verify selected themes were exported
            mock_export.assert_called_once_with(consultation)

            # Verify batch job was submitted for selected themes (default target)
            mock_batch.submit_job.assert_called_once_with(
                job_type="ASSIGN_THEMES",
                consultation_code=consultation.code,
                consultation_name=consultation.title,
                user_id=mock_batch.submit_job.call_args.kwargs["user_id"],
                model_name=consultation.model_name,
            )

            # Verify the default themes were created
            assert SelectedTheme.objects.filter(question=free_text_question, name="Other").exists()
            assert SelectedTheme.objects.filter(
                question=free_text_question, name="No Reason Given"
            ).exists()

            # Verify consultation stage advanced to assigning themes
            consultation.refresh_from_db()
            assert consultation.stage == Consultation.Stage.ASSIGNING_THEMES

    def test_assign_themes_no_selected_themes(self, client, staff_user_token, free_text_question):
        """Test assign themes fails when no user-created themes exist"""
        consultation = free_text_question.consultation
        consultation.stage = Consultation.Stage.FINALISING_THEMES
        consultation.save(update_fields=["stage"])

        url = reverse("consultations-assign-themes", kwargs={"pk": consultation.id})

        response = client.post(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400
        assert response.json()["error"] == "No selected themes found for at least one question."

    def test_assign_themes_no_selected_themes_non_admin(
        self, client, non_staff_user_token, free_text_question
    ):
        """Non-admin with correct stage but no themes gets the empty-themes error"""
        consultation = free_text_question.consultation
        consultation.stage = Consultation.Stage.FINALISING_THEMES
        consultation.save(update_fields=["stage"])

        url = reverse("consultations-assign-themes", kwargs={"pk": consultation.id})

        response = client.post(
            url,
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

        assert response.status_code == 400
        assert response.json()["error"] == "No selected themes found for at least one question."

    def test_assign_themes_wrong_stage_blocked_for_non_admin(
        self, client, non_staff_user_token, free_text_question
    ):
        """Non-admin users cannot regress a consultation from ANALYSIS by calling assign-themes"""
        consultation = free_text_question.consultation
        consultation.stage = Consultation.Stage.ANALYSIS
        consultation.save(update_fields=["stage"])

        url = reverse("consultations-assign-themes", kwargs={"pk": consultation.id})

        response = client.post(
            url,
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

        assert response.status_code == 400
        consultation.refresh_from_db()
        assert consultation.stage == Consultation.Stage.ANALYSIS


@pytest.mark.django_db
class TestImportFinalisedThemesEndpoint:
    def test_dry_run_returns_preview(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.FINALISING_THEMES)
        question_text = "Do you agree with the proposal?"
        source_q = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text=question_text
        )
        QuestionFactory(consultation=target, has_free_text=True, number=1, text=question_text)
        SelectedThemeFactory(question=source_q, name="Theme A", description="Desc A")
        SelectedThemeFactory(question=source_q, name="Theme B", description="Desc B")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})
        response = client.post(
            url + "?dry_run=true",
            {"source_consultation_id": str(source.id)},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is True
        assert data["questions"][0]["status"] == "will_import"
        assert data["questions"][0]["source_themes"] == ["Theme A", "Theme B"]
        assert SelectedTheme.objects.filter(question__consultation=target).count() == 0

    def test_import_creates_themes_and_updates_question_status(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.FINALISING_THEMES)
        question_text = "Do you agree with the proposal?"
        source_q = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text=question_text
        )
        target_q = QuestionFactory(
            consultation=target, has_free_text=True, number=1, text=question_text
        )
        SelectedThemeFactory(question=source_q, name="Theme A", description="Desc A")
        SelectedThemeFactory(question=source_q, name="Theme B", description="Desc B")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})

        with patch("consultations.api.views.consultation.export_selected_themes_to_s3"):
            response = client.post(
                url,
                {"source_consultation_id": str(source.id)},
                content_type="application/json",
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["dry_run"] is False
        assert data["total_themes_imported"] == 2
        assert SelectedTheme.objects.filter(question__consultation=target).count() == 2
        target_q.refresh_from_db()
        assert target_q.theme_status == Question.ThemeStatus.CONFIRMED

    def test_import_advances_stage_to_finalising_themes(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.SETUP)
        question_text = "Do you agree with the proposal?"
        source_q = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text=question_text
        )
        QuestionFactory(consultation=target, has_free_text=True, number=1, text=question_text)
        SelectedThemeFactory(question=source_q, name="Theme A", description="Desc A")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})

        with patch("consultations.api.views.consultation.export_selected_themes_to_s3"):
            response = client.post(
                url,
                {"source_consultation_id": str(source.id)},
                content_type="application/json",
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 200
        target.refresh_from_db()
        assert target.stage == Consultation.Stage.FINALISING_THEMES

    def test_skips_questions_with_existing_themes(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.FINALISING_THEMES)
        question_text = "Do you agree with the proposal?"
        source_q = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text=question_text
        )
        target_q = QuestionFactory(
            consultation=target, has_free_text=True, number=1, text=question_text
        )
        SelectedThemeFactory(question=source_q, name="Theme A", description="Desc A")
        SelectedThemeFactory(question=target_q, name="Existing", description="Already here")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})

        with patch("consultations.api.views.consultation.export_selected_themes_to_s3"):
            response = client.post(
                url,
                {"source_consultation_id": str(source.id)},
                content_type="application/json",
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["questions"][0]["status"] == "has_existing_themes"
        assert SelectedTheme.objects.filter(question=target_q).count() == 1
        assert SelectedTheme.objects.get(question=target_q).name == "Existing"
        assert "source_themes" not in data["questions"][0]

    def test_duplicate_target_questions_skipped(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.FINALISING_THEMES)
        question_text = "Do you agree?"
        source_q = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text=question_text
        )
        QuestionFactory(consultation=target, has_free_text=True, number=1, text=question_text)
        QuestionFactory(consultation=target, has_free_text=True, number=2, text=question_text)
        SelectedThemeFactory(question=source_q, name="Theme A", description="Desc A")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})

        with patch(
            "consultations.api.views.consultation.export_selected_themes_to_s3"
        ) as mock_export:
            response = client.post(
                url,
                {"source_consultation_id": str(source.id)},
                content_type="application/json",
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 400
        data = response.json()
        assert all(q["status"] == "duplicate_in_target" for q in data["questions"])
        assert SelectedTheme.objects.filter(question__consultation=target).count() == 0
        mock_export.assert_not_called()

    def test_duplicate_source_questions_skipped(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.FINALISING_THEMES)
        question_text = "Do you agree?"
        source_q1 = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text=question_text
        )
        QuestionFactory(consultation=source, has_free_text=True, number=2, text=question_text)
        QuestionFactory(consultation=target, has_free_text=True, number=1, text=question_text)
        SelectedThemeFactory(question=source_q1, name="Theme A", description="Desc A")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})

        with patch(
            "consultations.api.views.consultation.export_selected_themes_to_s3"
        ) as mock_export:
            response = client.post(
                url,
                {"source_consultation_id": str(source.id)},
                content_type="application/json",
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["questions"][0]["status"] == "duplicate_in_source"
        assert SelectedTheme.objects.filter(question__consultation=target).count() == 0
        mock_export.assert_not_called()

    def test_no_match_in_source(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.FINALISING_THEMES)
        source_q = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text="Source question"
        )
        QuestionFactory(consultation=target, has_free_text=True, number=1, text="Target question")
        SelectedThemeFactory(question=source_q, name="Theme A", description="Desc A")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})

        with patch(
            "consultations.api.views.consultation.export_selected_themes_to_s3"
        ) as mock_export:
            response = client.post(
                url,
                {"source_consultation_id": str(source.id)},
                content_type="application/json",
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["questions"][0]["status"] == "no_match_in_source"
        assert SelectedTheme.objects.filter(question__consultation=target).count() == 0
        mock_export.assert_not_called()

    def test_blocks_import_when_any_question_would_be_left_without_themes(
        self, client, staff_user_token
    ):
        """A mix of importable and unmatched questions blocks the whole import."""
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.FINALISING_THEMES)
        importable_text = "Do you agree?"
        source_q = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text=importable_text
        )
        QuestionFactory(consultation=target, has_free_text=True, number=1, text=importable_text)
        QuestionFactory(
            consultation=target, has_free_text=True, number=2, text="No match in source"
        )
        SelectedThemeFactory(question=source_q, name="Theme A", description="Desc A")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})

        with patch(
            "consultations.api.views.consultation.export_selected_themes_to_s3"
        ) as mock_export:
            response = client.post(
                url,
                {"source_consultation_id": str(source.id)},
                content_type="application/json",
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 400
        data = response.json()
        assert data["warnings"]["questions_without_themes"] == [2]
        # No partial import happened - not even the importable question was written
        assert SelectedTheme.objects.filter(question__consultation=target).count() == 0
        mock_export.assert_not_called()

    def test_unmatched_source_questions_in_warnings(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.FINALISING_THEMES)
        shared_text = "Shared question"
        source_only_text = "Only in source"
        source_q = QuestionFactory(
            consultation=source, has_free_text=True, number=1, text=shared_text
        )
        QuestionFactory(consultation=source, has_free_text=True, number=2, text=source_only_text)
        QuestionFactory(consultation=target, has_free_text=True, number=1, text=shared_text)
        SelectedThemeFactory(question=source_q, name="Theme A", description="Desc A")

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})
        response = client.post(
            url + "?dry_run=true",
            {"source_consultation_id": str(source.id)},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert source_only_text in data["warnings"]["unmatched_source_questions"]

    def test_rejects_same_consultation(self, client, staff_user_token):
        consultation = ConsultationFactory(title="Same", stage=Consultation.Stage.ANALYSIS)
        url = reverse("consultations-import-finalised-themes", kwargs={"pk": consultation.id})

        response = client.post(
            url,
            {"source_consultation_id": str(consultation.id)},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400

    def test_rejects_source_has_not_finalised_themes(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.FINALISING_THEMES)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.SETUP)

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})
        response = client.post(
            url,
            {"source_consultation_id": str(source.id)},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400
        assert response.json()["error"] == "Source consultation must have finalised themes"

    def test_rejects_target_has_already_finalised_themes(self, client, staff_user_token):
        source = ConsultationFactory(title="Source", stage=Consultation.Stage.ANALYSIS)
        target = ConsultationFactory(title="Target", stage=Consultation.Stage.ASSIGNING_THEMES)

        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})
        response = client.post(
            url,
            {"source_consultation_id": str(source.id)},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 400
        assert response.json()["error"] == "Target consultation has already finalised themes"

    def test_requires_admin(self, client):
        target = ConsultationFactory(title="Target")
        url = reverse("consultations-import-finalised-themes", kwargs={"pk": target.id})

        response = client.post(
            url,
            {"source_consultation_id": str(uuid4())},
            content_type="application/json",
        )

        assert response.status_code == 401


@pytest.mark.django_db
class TestEvaluationEndpoint:
    def test_returns_evaluation_stats(self, client, staff_user_token):
        """Returns per-question and summary evaluation stats."""
        consultation = ConsultationFactory()
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=5
        )

        respondents = [RespondentFactory(consultation=consultation) for _ in range(5)]
        responses = [
            ResponseFactory(question=question, respondent=r, free_text="text") for r in respondents
        ]

        policy_user = UserFactory(is_staff=False)
        ResponseReadBy.objects.create(response=responses[0], user=policy_user)
        ResponseReadBy.objects.create(response=responses[1], user=policy_user)

        theme_a = SelectedThemeFactory(question=question)
        theme_b = SelectedThemeFactory(question=question)

        # responses[0]: read and edited (AI assigned theme_a, human changed to theme_b)
        annotation = ResponseAnnotation.objects.create(response=responses[0])
        annotation.add_original_ai_themes([theme_a])
        annotation.set_human_reviewed_themes([theme_b], policy_user)

        # responses[1]: read but not edited (AI assigned theme_a, human kept it)
        annotation_unedited = ResponseAnnotation.objects.create(response=responses[1])
        annotation_unedited.add_original_ai_themes([theme_a])
        annotation_unedited.set_human_reviewed_themes([theme_a], policy_user)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        response = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert response.status_code == 200
        data = response.json()

        assert data["config"] == {"benchmark_f1": 0.75, "min_sample_size": 30}
        assert data["title"] == consultation.title
        assert data["summary"]["status"] == "insufficient_data"
        assert data["summary"]["responses"] == 5
        assert data["summary"]["responses_read"] == 2
        assert data["summary"]["responses_edited"] == 1

        assert len(data["questions"]) == 1
        q_data = data["questions"][0]
        assert q_data["status"] == "insufficient_data"
        assert q_data["responses"] == 5
        assert q_data["responses_read"] == 2
        assert q_data["responses_edited"] == 1
        assert q_data["f1"]["mean"] == 0.5

    def test_f1_score_perfect_agreement(self, client, staff_user_token):
        """F1 is 1.0 when themes are edited back to match the original AI assignment."""
        consultation = ConsultationFactory()
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=1
        )
        respondent = RespondentFactory(consultation=consultation)
        response_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")

        user_a = UserFactory(is_staff=False)
        user_b = UserFactory(is_staff=False)
        ResponseReadBy.objects.create(response=response_obj, user=user_a)
        theme_a = SelectedThemeFactory(question=question)
        theme_b = SelectedThemeFactory(question=question)
        annotation = ResponseAnnotation.objects.create(response=response_obj)
        annotation.add_original_ai_themes([theme_a])
        annotation.set_human_reviewed_themes([theme_b], user_a)
        annotation.set_human_reviewed_themes([theme_a], user_b)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        assert resp.json()["questions"][0]["f1"]["mean"] == 1.0

    def test_f1_score_no_agreement(self, client, staff_user_token):
        """F1 is 0 when human reads, removes all AI themes and adds different ones."""
        consultation = ConsultationFactory()
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=1
        )
        respondent = RespondentFactory(consultation=consultation)
        response_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")

        policy_user = UserFactory(is_staff=False)
        ResponseReadBy.objects.create(response=response_obj, user=policy_user)
        ai_theme = SelectedThemeFactory(question=question)
        human_theme = SelectedThemeFactory(question=question)
        annotation = ResponseAnnotation.objects.create(response=response_obj)
        annotation.add_original_ai_themes([ai_theme])
        annotation.set_human_reviewed_themes([human_theme], policy_user)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        assert resp.json()["questions"][0]["f1"]["mean"] == 0.0

    def test_f1_confidence_intervals(self, client, staff_user_token):
        """Returns confidence intervals with realistic sample size (30+ read)."""
        consultation = ConsultationFactory()
        policy_user = UserFactory(is_staff=False)

        # Question 1: below benchmark (20 agree, 10 disagree → F1 = 0.67)
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=35
        )
        theme = SelectedThemeFactory(question=question)
        other_theme = SelectedThemeFactory(question=question)

        for _ in range(20):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=policy_user)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme])
            annotation.set_human_reviewed_themes([theme], policy_user)
            annotation.mark_human_reviewed(policy_user)

        for _ in range(10):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=policy_user)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme])
            annotation.set_human_reviewed_themes([other_theme], policy_user)

        # Question 2: meets benchmark (28 agree, 2 disagree → F1 = 0.93)
        question_2 = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=35
        )
        theme_2 = SelectedThemeFactory(question=question_2)
        other_theme_2 = SelectedThemeFactory(question=question_2)

        for _ in range(28):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question_2, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=policy_user)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme_2])
            annotation.set_human_reviewed_themes([theme_2], policy_user)
            annotation.mark_human_reviewed(policy_user)

        for _ in range(2):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question_2, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=policy_user)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme_2])
            annotation.set_human_reviewed_themes([other_theme_2], policy_user)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        data = resp.json()

        # Question 1: below benchmark
        q1_data = data["questions"][0]
        assert q1_data["status"] == "below_benchmark"
        assert q1_data["f1"]["mean"] == 0.67
        assert q1_data["f1"]["ci_lower"] == 0.5
        assert q1_data["f1"]["ci_upper"] == 0.84
        assert q1_data["f1"]["approximate"] is False

        # Question 2: meets benchmark
        q2_data = data["questions"][1]
        assert q2_data["status"] == "meets_benchmark"
        assert q2_data["f1"]["mean"] == 0.93
        assert q2_data["f1"]["ci_lower"] == 0.84
        assert q2_data["f1"]["ci_upper"] == 1.0
        assert q2_data["f1"]["approximate"] is False

    def test_f1_suppresses_ci_below_30_responses(self, client, staff_user_token):
        """Returns null confidence internals when fewer than 30 responses read."""
        consultation = ConsultationFactory()
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=10
        )
        policy_user = UserFactory(is_staff=False)
        theme = SelectedThemeFactory(question=question)
        other_theme = SelectedThemeFactory(question=question)

        for _ in range(5):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=policy_user)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme])
            annotation.set_human_reviewed_themes([theme], policy_user)

        for _ in range(3):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=policy_user)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme])
            annotation.set_human_reviewed_themes([other_theme], policy_user)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["questions"][0]["status"] == "insufficient_data"
        f1_data = data["questions"][0]["f1"]
        assert f1_data["mean"] == 0.62
        assert f1_data["ci_lower"] is None
        assert f1_data["ci_upper"] is None
        assert f1_data["approximate"] is True

    def test_sample_average_f1_with_varying_theme_counts(self, client, staff_user_token):
        """
        Returns sample-average F1 which weights each response equally
        regardless of theme count.
        """
        consultation = ConsultationFactory()
        policy_user = UserFactory(is_staff=False)
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=10
        )
        theme_a = SelectedThemeFactory(question=question)
        theme_b = SelectedThemeFactory(question=question)
        theme_c = SelectedThemeFactory(question=question)

        # Response 1: AI assigns 3 themes, human keeps 2 (removes theme_c)
        # TP=2, FP=1, FN=0 → P=2/3, R=1.0, F1=0.8
        r1 = RespondentFactory(consultation=consultation)
        resp1 = ResponseFactory(question=question, respondent=r1, free_text="text")
        ResponseReadBy.objects.create(response=resp1, user=policy_user)
        ann1 = ResponseAnnotation.objects.create(response=resp1)
        ann1.add_original_ai_themes([theme_a, theme_b, theme_c])
        ann1.set_human_reviewed_themes([theme_a, theme_b], policy_user)
        ann1.mark_human_reviewed(policy_user)

        # Response 2: AI assigns 1 theme, human replaces it
        # TP=0, FP=1, FN=1 → F1=0.0
        r2 = RespondentFactory(consultation=consultation)
        resp2 = ResponseFactory(question=question, respondent=r2, free_text="text")
        ResponseReadBy.objects.create(response=resp2, user=policy_user)
        ann2 = ResponseAnnotation.objects.create(response=resp2)
        ann2.add_original_ai_themes([theme_a])
        ann2.set_human_reviewed_themes([theme_b], policy_user)
        ann2.mark_human_reviewed(policy_user)

        # Response 3: AI assigns 2 themes, human keeps both
        # TP=2, FP=0, FN=0 → F1=1.0
        r3 = RespondentFactory(consultation=consultation)
        resp3 = ResponseFactory(question=question, respondent=r3, free_text="text")
        ResponseReadBy.objects.create(response=resp3, user=policy_user)
        ann3 = ResponseAnnotation.objects.create(response=resp3)
        ann3.add_original_ai_themes([theme_a, theme_b])
        ann3.set_human_reviewed_themes([theme_a, theme_b], policy_user)
        ann3.mark_human_reviewed(policy_user)

        # Response 4: AI assigns 1 theme, human removes all
        # TP=0, FP=0, FN=1 → F1=0.0
        r4 = RespondentFactory(consultation=consultation)
        resp4 = ResponseFactory(question=question, respondent=r4, free_text="text")
        ResponseReadBy.objects.create(response=resp4, user=policy_user)
        ann4 = ResponseAnnotation.objects.create(response=resp4)
        ann4.add_original_ai_themes([theme_a])
        ann4.set_human_reviewed_themes([], policy_user)
        ann4.mark_human_reviewed(policy_user)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        q_data = resp.json()["questions"][0]
        f1_data = q_data["f1"]
        assert f1_data["mean"] == 0.45  # (0.8 + 0.0 + 1.0 + 0.0) / 4 = 0.45
        assert q_data["responses_edited"] == 3

    def test_excludes_generic_themes(self, client, staff_user_token):
        """f1_excl_generic excludes 'Other' and 'No Reason Given' themes."""
        consultation = ConsultationFactory()
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=1
        )
        respondent = RespondentFactory(consultation=consultation)
        response_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")

        policy_user = UserFactory(is_staff=False)
        ResponseReadBy.objects.create(response=response_obj, user=policy_user)
        real_theme = SelectedThemeFactory(question=question, name="Real Theme")
        other_theme = SelectedThemeFactory(question=question, name="Other")

        annotation = ResponseAnnotation.objects.create(response=response_obj)
        annotation.add_original_ai_themes([real_theme, other_theme])
        annotation.set_human_reviewed_themes([real_theme], policy_user)
        annotation.mark_human_reviewed(policy_user)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        q_data = resp.json()["questions"][0]
        # Excluding generic: AI had {real}, human has {real} → perfect agreement
        assert q_data["f1"]["mean"] == 1.0
        # With all themes: AI had {real, other}, human has {real} → TP=1, FP=1, FN=0 → F1=0.67
        assert q_data["f1_all_themes"]["mean"] == 0.67

    def test_excludes_staff_from_read_and_edit_counts(self, client, staff_user, staff_user_token):
        """Staff reads and edits are not counted in evaluation stats."""
        consultation = ConsultationFactory()
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=1
        )
        respondent = RespondentFactory(consultation=consultation)
        response_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")

        ResponseReadBy.objects.create(response=response_obj, user=staff_user)
        theme = SelectedThemeFactory(question=question)
        annotation = ResponseAnnotation.objects.create(response=response_obj)
        annotation.add_original_ai_themes([theme])
        annotation.set_human_reviewed_themes([theme], staff_user)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        assert resp.json()["summary"]["responses_read"] == 0
        assert resp.json()["summary"]["responses_edited"] == 0

    def test_std_zero_returns_no_ci(self, client, staff_user_token):
        """When all F1 scores are identical (std=0), returns null confidence intervals."""
        consultation = ConsultationFactory()
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=35
        )
        policy_user = UserFactory(is_staff=False)
        theme = SelectedThemeFactory(question=question)

        for _ in range(30):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=policy_user)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme])
            annotation.set_human_reviewed_themes([theme], policy_user)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        f1_data = resp.json()["questions"][0]["f1"]
        assert f1_data["mean"] == 1.0
        assert f1_data["ci_lower"] is None
        assert f1_data["ci_upper"] is None
        assert f1_data["approximate"] is False

    def test_filter_by_user_ids(self, client, staff_user_token):
        """Filters evaluation stats to only responses read by specified users."""
        consultation = ConsultationFactory()
        question = QuestionFactory(
            consultation=consultation, has_free_text=True, free_text_response_count=4
        )

        user_a = UserFactory(is_staff=False)
        user_b = UserFactory(is_staff=False)
        theme = SelectedThemeFactory(question=question)
        other_theme = SelectedThemeFactory(question=question)

        # user_a reads 2 responses — perfect agreement
        for _ in range(2):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=user_a)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme])
            annotation.set_human_reviewed_themes([theme], user_a)

        # user_b reads 2 responses — no agreement
        for _ in range(2):
            respondent = RespondentFactory(consultation=consultation)
            resp_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")
            ResponseReadBy.objects.create(response=resp_obj, user=user_b)
            annotation = ResponseAnnotation.objects.create(response=resp_obj)
            annotation.add_original_ai_themes([theme])
            annotation.set_human_reviewed_themes([other_theme], user_b)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})

        # Filter to user_a only — should show F1=1.0
        resp = client.get(
            url,
            query_params={"user_ids": str(user_a.id)},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["responses_read"] == 2
        assert data["questions"][0]["f1"]["mean"] == 1.0

        # Filter to user_b only — should show F1=0.0
        resp = client.get(
            url,
            query_params={"user_ids": str(user_b.id)},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["responses_read"] == 2
        assert data["questions"][0]["f1"]["mean"] == 0.0

        # No filter — should show all 4 reads, blended F1
        resp = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"]["responses_read"] == 4
        assert data["questions"][0]["f1"]["mean"] == 0.5

    def test_returns_available_users(self, client, staff_user_token):
        """Response includes list of non-staff users who have read responses."""
        consultation = ConsultationFactory()
        question = QuestionFactory(consultation=consultation, has_free_text=True)

        user_a = UserFactory(is_staff=False, email="alice@example.com")
        user_b = UserFactory(is_staff=False, email="bob@example.com")
        user_c = UserFactory(is_staff=True, email="staff@example.com")

        respondent = RespondentFactory(consultation=consultation)
        resp_obj = ResponseFactory(question=question, respondent=respondent, free_text="text")
        ResponseReadBy.objects.create(response=resp_obj, user=user_a)
        ResponseReadBy.objects.create(response=resp_obj, user=user_b)
        ResponseReadBy.objects.create(response=resp_obj, user=user_c)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert resp.status_code == 200
        users = resp.json()["users"]
        user_emails = {u["email"] for u in users}
        assert "alice@example.com" in user_emails
        assert "bob@example.com" in user_emails
        assert "staff@example.com" not in user_emails

    def test_requires_admin(self, client):
        """Non-admin users added to the consultation cannot access evaluation endpoint."""
        from rest_framework_simplejwt.tokens import RefreshToken

        consultation = ConsultationFactory()
        policy_user = UserFactory(is_staff=False)
        consultation.users.add(policy_user)
        token = str(RefreshToken.for_user(policy_user).access_token)

        url = reverse("consultations-evaluation", kwargs={"pk": consultation.id})
        resp = client.get(url, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
