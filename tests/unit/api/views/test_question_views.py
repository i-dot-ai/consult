import pytest
from django.urls import reverse

from consultation_analyser.consultations.models import Question
from consultation_analyser.factories import QuestionFactory, RespondentFactory, ResponseFactory


@pytest.mark.django_db
class TestQuestionViewSet:
    def test_get_theme_information_no_themes(
        self, client, consultation_user_token, free_text_question
    ):
        """Test API endpoint returns empty themes list when no themes exist"""
        url = reverse(
            "question-theme-information",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "themes" in data
        assert data["themes"] == []

    def test_get_theme_information_with_themes(
        self, client, consultation_user_token, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint returns theme information correctly"""
        url = reverse(
            "question-theme-information",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
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

    def test_get_free_text_question(
        self, client, consultation_user, free_text_question, consultation_user_token
    ):
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
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["question_text"] == free_text_question.text
        assert data["total_responses"] == 3
        assert data["multiple_choice_answer"] == []

    def test_get_multiple_choice_question(
        self,
        client,
        consultation_user,
        multi_choice_responses,
        multi_choice_question,
        consultation_user_token,
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
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["question_text"] == multi_choice_question.text
        assert data["total_responses"] == 2
        answer_counts = {x["text"]: x["response_count"] for x in data["multiple_choice_answer"]}
        assert answer_counts == {"blue": 1, "green": 0, "red": 2}

    def test_patch_question_theme_status(
        self, client, consultation_user, free_text_question, consultation_user_token
    ):
        """Test API endpoint for patching a question's theme status"""
        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        assert free_text_question.theme_status == Question.ThemeStatus.CONFIRMED
        response = client.patch(
            url,
            data={"theme_status": Question.ThemeStatus.DRAFT},
            content_type="application/json",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 200
        free_text_question.refresh_from_db()
        assert free_text_question.theme_status == Question.ThemeStatus.DRAFT

    def test_patch_question_invalid_theme_status(
        self, client, consultation_user, free_text_question, consultation_user_token
    ):
        """Test API endpoint for patching a question's theme status with invalid value"""
        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        assert free_text_question.theme_status == Question.ThemeStatus.CONFIRMED
        response = client.patch(
            url,
            data={"theme_status": "INVALID"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 400
        free_text_question.refresh_from_db()
        assert free_text_question.theme_status == Question.ThemeStatus.CONFIRMED

    @pytest.mark.parametrize("has_free_text", [True, False, ""])
    def test_filter(self, client, consultation_user_token, consultation, has_free_text):
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
            headers={"Authorization": f"Bearer {consultation_user_token}"},
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
        consultation_user_token,
        consultation,
        free_text_question,
        multi_choice_question,
    ):
        """Test the question list endpoint returns the questions in the right order"""

        url = reverse("question-list", kwargs={"consultation_pk": consultation.id})

        # Filter by has_free_text=True
        response = client.get(
            url,
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert [x["number"] for x in data["results"]] == [1, 2]
