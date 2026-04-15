import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import Question
from factories import (
    MultiChoiceAnswerFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
)


@pytest.mark.django_db
class TestQuestionViewSet:
    def test_get_theme_information_no_themes(self, client, staff_user_token, free_text_question):
        """Test API endpoint returns empty themes list when no themes exist"""
        url = reverse(
            "question-themes",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "themes" in data
        assert data["themes"] == []

    def test_get_theme_information_with_themes(
        self, client, staff_user_token, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint returns theme information correctly"""
        url = reverse(
            "question-themes",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "themes" in data
        themes = data["themes"]

        assert len(themes) == 2
        theme_names = {t["name"] for t in themes}
        assert theme_names == {"Theme A", "Theme B"}

        # Verify theme structure
        for theme_data in themes:
            assert "id" in theme_data
            assert "name" in theme_data
            assert "description" in theme_data
            assert "count" in theme_data

    def test_get_themes_with_counts(
        self, client, staff_user_token, free_text_question, theme_a, theme_b
    ):
        """Test themes endpoint returns correct response counts per theme"""
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)
        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        # Assign theme_a to both responses, theme_b to only one
        ann1 = ResponseAnnotationFactoryNoThemes(response=response1)
        ann1.add_original_ai_themes([theme_a, theme_b])
        ann2 = ResponseAnnotationFactoryNoThemes(response=response2)
        ann2.add_original_ai_themes([theme_a])

        url = reverse(
            "question-themes",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        themes = {t["name"]: t["count"] for t in response.json()["themes"]}
        assert themes["Theme A"] == 2
        assert themes["Theme B"] == 1

    def test_get_themes_filtered_by_demographic(
        self,
        client,
        staff_user_token,
        free_text_question,
        theme_a,
        individual_demographic,
        group_demographic,
    ):
        """Test themes endpoint filters counts when demographic filter is applied"""
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent1.demographics.set([individual_demographic])
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2.demographics.set([group_demographic])

        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        ann1 = ResponseAnnotationFactoryNoThemes(response=response1)
        ann1.add_original_ai_themes([theme_a])
        ann2 = ResponseAnnotationFactoryNoThemes(response=response2)
        ann2.add_original_ai_themes([theme_a])

        url = reverse(
            "question-themes",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        # Filter to only individual respondents
        response = client.get(
            url,
            query_params={"demographics": individual_demographic.pk},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        themes = {t["name"]: t["count"] for t in response.json()["themes"]}
        assert themes["Theme A"] == 1

    def test_get_free_text_question(self, client, staff_user, free_text_question, staff_user_token):
        """Test API endpoint returns question information correctly"""
        # Add a known response count with free text
        for i in range(3):
            respondent = RespondentFactory(consultation=free_text_question.consultation)
            ResponseFactory(
                question=free_text_question, respondent=respondent, free_text=f"Response {i}"
            )

        # Update the total_responses count
        free_text_question.update_total_responses()

        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["question_text"] == free_text_question.text
        assert data["total_responses"] == 3
        assert data["multiple_choice_answer"] == []

    def test_get_multiple_choice_question(
        self,
        client,
        staff_user,
        multi_choice_responses,
        multi_choice_question,
        staff_user_token,
    ):
        """Test API endpoint returns question information correctly"""

        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": multi_choice_question.consultation.id,
                "pk": multi_choice_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["question_text"] == multi_choice_question.text
        assert data["total_responses"] == 2
        answer_counts = {x["text"]: x["response_count"] for x in data["multiple_choice_answer"]}
        assert answer_counts == {"blue": 1, "green": 0, "red": 2}

    def test_patch_question_theme_status(
        self, client, staff_user, free_text_question, staff_user_token
    ):
        """Test API endpoint for patching a question's theme status"""
        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        assert free_text_question.theme_status == Question.ThemeStatus.DRAFT
        response = client.patch(
            url,
            data={"theme_status": Question.ThemeStatus.CONFIRMED},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        free_text_question.refresh_from_db()
        assert free_text_question.theme_status == Question.ThemeStatus.CONFIRMED

    def test_patch_question_invalid_theme_status(
        self, client, staff_user, free_text_question, staff_user_token
    ):
        """Test API endpoint for patching a question's theme status with invalid value"""
        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        assert free_text_question.theme_status == Question.ThemeStatus.DRAFT
        response = client.patch(
            url,
            data={"theme_status": "INVALID"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 400
        free_text_question.refresh_from_db()
        assert free_text_question.theme_status == Question.ThemeStatus.DRAFT

    @pytest.mark.parametrize("has_free_text", [True, False, ""])
    def test_filter(self, client, staff_user_token, consultation, has_free_text):
        """Test filtering questions by has_free_text"""

        # Create questions with different free text settings
        _free_text_question = QuestionFactory(
            consultation=consultation, has_free_text=True, text="Free text question"
        )
        _multi_choice_question = QuestionFactory(
            consultation=consultation, has_free_text=False, text="Multi choice question"
        )

        url = reverse("question-list", kwargs={"consultation_pk": consultation.id})

        # Filter by has_free_text=True
        response = client.get(
            url,
            {"has_free_text": has_free_text},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        results = data.get("results", data)

        if has_free_text == "":
            # should return both
            assert len(results) == 2
        else:
            # should return just one question
            assert len(results) == 1
            assert results[0]["has_free_text"] == has_free_text

    def test_question_list(
        self,
        client,
        staff_user_token,
        consultation,
        free_text_question,
        multi_choice_question,
    ):
        """Test the question list endpoint returns the questions in the right order"""

        url = reverse("question-list", kwargs={"consultation_pk": consultation.id})

        # Filter by has_free_text=True
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert [x["number"] for x in data["results"]] == [1, 2]

    def test_show_next_response_happy_path(
        self,
        client,
        staff_user_token,
        consultation,
        free_text_question,
        human_reviewed_annotation,
    ):
        """test show_next_response finds the next response that is free text but not already reviewed"""
        url = reverse(
            "question-show-next-response",
            kwargs={
                "consultation_pk": consultation.id,
                "pk": free_text_question.id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["next_response"]["id"] == str(human_reviewed_annotation.response.id)
        assert data["has_free_text"] is True
        assert data["message"] == "Next response found."

    def test_show_next_response_no_responses_left_to_review(
        self,
        client,
        staff_user_token,
        consultation,
        free_text_question,
        un_reviewed_annotation,
    ):
        """test show_next_response finds the next response that is free text but not already reviewed"""
        url = reverse(
            "question-show-next-response",
            kwargs={
                "consultation_pk": consultation.id,
                "pk": free_text_question.id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["next_response"] is None
        assert data["has_free_text"] is True
        assert data["message"] == "This question does not have free text responses"

    def test_show_next_response_no_free_text(
        self,
        client,
        staff_user_token,
        consultation,
        multi_choice_question,
    ):
        """test show_next_response returns nothing if there are no free text questions"""
        url = reverse(
            "question-show-next-response",
            kwargs={
                "consultation_pk": consultation.id,
                "pk": multi_choice_question.id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["next_response"] is None
        assert data["has_free_text"] is False
        assert data["message"] == "This question does not have free text responses."

    def test_permission_requires_consultation_access(self, client, free_text_question):
        """Test that QuestionViewSet requires consultation access"""
        from factories import UserFactory

        # Create a user who is NOT assigned to any consultation
        isolated_user = UserFactory(is_staff=False)
        refresh = RefreshToken.for_user(isolated_user)
        token = str(refresh.access_token)

        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
        )
        isolated_user.delete()
        assert response.status_code == 403

    def test_delete_method_supported(self, client, staff_user_token, free_text_question):
        """Test that DELETE method is now supported"""
        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.delete(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        # Should return 204 for successful deletion, not 405 Method Not Allowed
        assert response.status_code == 204

        # Verify question was actually deleted
        assert not Question.objects.filter(id=free_text_question.id).exists()

    def test_unsupported_http_methods(self, client, staff_user_token, free_text_question):
        """Test that unsupported HTTP methods return 405"""
        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )

        # POST should not be supported (only get, patch, delete)
        response = client.post(
            url,
            data={"theme_status": "confirmed"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 405

        # PUT should not be supported (only get, patch, delete)
        response = client.put(
            url,
            data={"theme_status": "confirmed"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 405

    def test_patch_hybrid_question_with_multichoice(
        self, client, staff_user, consultation, staff_user_token
    ):
        """Test PATCH request on hybrid question with multiple choice answers"""
        hybrid_question = QuestionFactory(
            consultation=consultation,
            has_free_text=True,
            has_multiple_choice=True,
            number=1,
            text="whats your favourite colour",
        )
        MultiChoiceAnswerFactory.create(question=hybrid_question, text="red")

        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": consultation.id,
                "pk": hybrid_question.id,
            },
        )

        response = client.patch(
            url,
            data={"theme_status": Question.ThemeStatus.CONFIRMED},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert response.json()["theme_status"] == "confirmed"


@pytest.mark.django_db
class TestQuestionResponseViewSet:
    """Tests for the nested /questions/{qid}/responses/ route"""

    def test_question_responses_returns_scoped_results(
        self, client, staff_user_token, consultation, free_text_question
    ):
        """Test nested route only returns responses for the given question"""
        question_2 = QuestionFactory(consultation=consultation, has_free_text=True, number=3)

        respondent1 = RespondentFactory(consultation=consultation)
        respondent2 = RespondentFactory(consultation=consultation)
        ResponseFactory(question=free_text_question, respondent=respondent1)
        ResponseFactory(question=question_2, respondent=respondent2)

        url = reverse(
            "question-response-list",
            kwargs={
                "consultation_pk": consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filtered_total"] == 1
        assert data["respondents_total"] == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_question_responses_pagination(self, client, staff_user_token, free_text_question):
        """Test nested route supports pagination"""
        for _ in range(5):
            respondent = RespondentFactory(consultation=free_text_question.consultation)
            ResponseFactory(question=free_text_question, respondent=respondent)

        url = reverse(
            "question-response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            query_params={"page_size": 2, "page": 1},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["all_respondents"]) == 2
        assert data["has_more_pages"] is True
        assert data["filtered_total"] == 5

    def test_question_responses_with_theme_filter(
        self, client, staff_user_token, free_text_question, theme_a
    ):
        """Test nested route works with theme filters"""
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)
        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        ResponseFactory(question=free_text_question, respondent=respondent2)

        annotation = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation.add_original_ai_themes([theme_a])

        url = reverse(
            "question-response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            query_params={"themeFilters": str(theme_a.id)},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filtered_total"] == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)
