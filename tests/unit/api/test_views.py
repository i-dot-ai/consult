import json
from datetime import datetime
from uuid import uuid4

import orjson
import pytest
from django.urls import reverse

from consultation_analyser.consultations.models import ResponseAnnotation, ResponseAnnotationTheme
from consultation_analyser.factories import (
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
)
from tests.utils import build_url


@pytest.mark.django_db
class TestDemographicOptionsAPIView:
    def test_get_demographic_options_empty(self, client, consultation_user, free_text_question):
        """Test API endpoint returns empty options when no demographic data exists"""
        client.force_login(consultation_user)
        url = reverse(
            "consultations-demographic-options",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(url)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_demographic_options_with_data(self, client, consultation_user, free_text_question):
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

        client.force_login(consultation_user)
        url = reverse(
            "consultations-demographic-options",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(url)

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
        assert data == expected

    def test_permission_required(self, client, free_text_question):
        """Test API endpoint requires proper permissions"""
        url = reverse(
            "consultations-demographic-options",
            kwargs={"pk": free_text_question.consultation.id},
        )
        response = client.get(url)
        assert response.status_code == 401

    def test_invalid_consultation_slug(self, client, consultation_user):
        """Test API endpoint with invalid consultation slug"""
        client.force_login(consultation_user)
        url = reverse("consultations-demographic-options", kwargs={"pk": uuid4()})
        response = client.get(url)
        assert response.status_code == 404  # NOT FOUND


@pytest.mark.django_db
class TestDemographicAggregationsAPIView:
    def test_get_demographic_aggregations_empty(
        self, client, consultation_user, free_text_question
    ):
        """Test API endpoint returns empty aggregations when no data exists"""
        client.force_login(consultation_user)
        url = reverse(
            "response-demographic-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "demographic_aggregations" in data
        assert data["demographic_aggregations"] == {}

    def test_get_demographic_aggregations_with_data(
        self, client, consultation_user, free_text_question
    ):
        """Test API endpoint returns demographic aggregations correctly"""
        # Create respondents with different demographic data
        respondent1 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"gender": "male", "age_group": "25-34", "region": "north"},
        )
        respondent2 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"gender": "female", "age_group": "25-34", "region": "south"},
        )
        respondent3 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"gender": "male", "age_group": "35-44", "region": "north"},
        )

        # Create responses for each respondent
        ResponseFactory(respondent=respondent1, question=free_text_question)
        ResponseFactory(respondent=respondent2, question=free_text_question)
        ResponseFactory(respondent=respondent3, question=free_text_question)

        client.force_login(consultation_user)
        url = reverse(
            "response-demographic-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "demographic_aggregations" in data

        aggregations = data["demographic_aggregations"]
        assert aggregations["gender"]["male"] == 2
        assert aggregations["gender"]["female"] == 1
        assert aggregations["age_group"]["25-34"] == 2
        assert aggregations["age_group"]["35-44"] == 1
        assert aggregations["region"]["north"] == 2
        assert aggregations["region"]["south"] == 1

    def test_get_demographic_aggregations_with_filters(
        self, client, consultation_user, free_text_question
    ):
        """Test API endpoint applies demographic filters correctly"""
        # Create respondents with different demographics
        respondent1 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": True, "region": "north"},
        )
        respondent2 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": False, "region": "south"},
        )

        ResponseFactory(question=free_text_question, respondent=respondent1)
        ResponseFactory(question=free_text_question, respondent=respondent2)

        client.force_login(consultation_user)
        url = reverse(
            "response-demographic-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        # Filter by individual=true
        response = client.get(url + "?demoFilters=individual:true")

        assert response.status_code == 200
        data = response.json()

        # Should only include data from individual=True respondent
        aggregations = data["demographic_aggregations"]
        assert aggregations["individual"]["True"] == 1
        assert aggregations["region"]["north"] == 1
        # Should not have data from individual=False respondent
        assert "False" not in aggregations["individual"]
        assert "south" not in aggregations["region"]

        response = client.get(url + "?demoFilters=individual:true&demoFilters=individual:false")

        assert response.status_code == 200
        data = response.json()
        assert data["demographic_aggregations"]["individual"] == {"True": 1, "False": 1}
        assert data["demographic_aggregations"]["region"] == {"north": 1, "south": 1}


@pytest.mark.django_db
class TestThemeInformationAPIView:
    def test_get_theme_information_no_themes(self, client, consultation_user, free_text_question):
        """Test API endpoint returns empty themes list when no themes exist"""
        client.force_login(consultation_user)
        url = reverse(
            "question-theme-information",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "themes" in data
        assert data["themes"] == []

    def test_get_theme_information_with_themes(
        self, client, consultation_user, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint returns theme information correctly"""
        client.force_login(consultation_user)
        url = reverse(
            "question-theme-information",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(url)

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


@pytest.mark.django_db
class TestThemeAggregationsAPIView:
    def test_get_theme_aggregations_no_responses(
        self, client, consultation_user, free_text_question
    ):
        """Test API endpoint returns empty aggregations when no responses exist"""
        client.force_login(consultation_user)
        url = reverse(
            "response-theme-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "theme_aggregations" in data
        assert data["theme_aggregations"] == {}

    def test_get_theme_aggregations_with_responses(
        self, client, consultation_user, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint returns theme aggregations correctly"""
        # Create respondents and responses
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)

        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        # Create annotations with themes
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme_a])

        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme_a, theme_b])

        client.force_login(consultation_user)
        url = reverse(
            "response-theme-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "theme_aggregations" in data

        aggregations = data["theme_aggregations"]
        assert aggregations[str(theme_a.id)] == 2  # Theme A appears in 2 responses
        assert aggregations[str(theme_b.id)] == 1  # Theme B appears in 1 response

    def test_get_theme_aggregations_with_filters(
        self, client, consultation_user, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint applies theme filtering correctly"""
        # Create responses with different theme combinations
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)

        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        # Response 1: has theme1 and theme2
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme_a, theme_b])

        # Response 2: has only theme1
        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme_a])

        client.force_login(consultation_user)
        url = reverse(
            "response-theme-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        # Filter by theme1 AND theme2 - should only return response1
        response = client.get(url + f"?themeFilters={theme_a.id},{theme_b.id}")

        assert response.status_code == 200
        data = response.json()

        # Should only show counts from responses that have BOTH themes
        aggregations = data["theme_aggregations"]
        assert aggregations[str(theme_a.id)] == 1  # Only response1 has both themes
        assert aggregations[str(theme_b.id)] == 1  # Only response1 has both themes


@pytest.mark.django_db
class TestFilteredResponsesAPIView:
    def test_get_filtered_responses_basic(self, client, consultation_user, free_text_question):
        """Test API endpoint returns filtered responses correctly"""
        # Create test data
        respondent = RespondentFactory(
            consultation=free_text_question.consultation, demographics={"individual": True}
        )
        ResponseFactory(
            question=free_text_question, respondent=respondent, free_text="Test response"
        )

        client.force_login(consultation_user)
        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200

        # Parse the response
        data = orjson.loads(response.content)

        assert "all_respondents" in data
        assert "respondents_total" in data
        assert "filtered_total" in data
        assert len(data["all_respondents"]) == 1
        assert data["respondents_total"] == 1
        assert data["filtered_total"] == 1

        # Verify respondent data structure
        respondent_data = data["all_respondents"][0]
        assert respondent_data["identifier"] == str(respondent.identifier)
        assert respondent_data["free_text_answer_text"] == "Test response"
        assert respondent_data["demographic_data"] == {"individual": True}

    def test_get_filtered_responses_with_pagination(
        self, client, consultation_user, free_text_question
    ):
        """Test API endpoint pagination"""
        # Create multiple respondents
        for i in range(5):
            respondent = RespondentFactory(consultation=free_text_question.consultation)
            ResponseFactory(question=free_text_question, respondent=respondent)

        client.force_login(consultation_user)
        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(url + "?page_size=2&page=1")

        assert response.status_code == 200

        data = orjson.loads(response.content)

        assert len(data["all_respondents"]) == 2
        assert data["has_more_pages"]
        assert data["filtered_total"] == 5

    def test_get_filtered_responses_with_demographic_filters(
        self, client, consultation_user, free_text_question
    ):
        """Test API endpoint with demographic filtering"""
        # Create respondents with different demographics
        respondent1 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": True, "region": "north"},
        )
        respondent2 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": False, "region": "south"},
        )

        ResponseFactory(question=free_text_question, respondent=respondent1)
        ResponseFactory(question=free_text_question, respondent=respondent2)

        client.force_login(consultation_user)
        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        # Filter by individual=true
        response = client.get(url + "?demoFilters=individual:true")

        assert response.status_code == 200

        data = orjson.loads(response.content)

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == 1  # Filtered to individuals only
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_get_filtered_responses_with_theme_filters(
        self, client, consultation_user, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint with theme filtering using AND logic"""
        # Create responses with different theme combinations
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)
        respondent3 = RespondentFactory(consultation=free_text_question.consultation)

        response1 = ResponseFactory(
            question=free_text_question, respondent=respondent1, free_text="Response 1"
        )
        response2 = ResponseFactory(
            question=free_text_question, respondent=respondent2, free_text="Response 2"
        )
        response3 = ResponseFactory(
            question=free_text_question, respondent=respondent3, free_text="Response 3"
        )

        # Response 1: has theme and theme2
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme_a, theme_b])

        # Response 2: has only theme
        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme_a])

        # Response 3: has only theme2
        annotation3 = ResponseAnnotationFactoryNoThemes(response=response3)
        annotation3.add_original_ai_themes([theme_b])

        client.force_login(consultation_user)
        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        # Filter by theme AND theme2 - should only return response1
        response = client.get(url + f"?themeFilters={theme_a.id},{theme_b.id}")

        assert response.status_code == 200

        data = orjson.loads(response.content)

        # assert data["respondents_total"] == 3  # Total respondents
        assert data["filtered_total"] == 1  # Only response1 has both themes
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_get_filtered_responses_with_respondent_filters(
        self,
        client,
        consultation_user,
        free_text_question,
        consultation_user_token,
        respondent_1,
        respondent_2,
    ):
        """Test API endpoint with theme filtering using AND logic"""
        # Create responses with different theme combinations

        _ = ResponseFactory(
            question=free_text_question, respondent=respondent_1, free_text="Response 1"
        )
        _ = ResponseFactory(
            question=free_text_question, respondent=respondent_2, free_text="Response 2"
        )

        client.force_login(consultation_user)

        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        # Filter by respondent1 - should only return response1
        response = client.get(
            url + f"?respondent_id={respondent_1.id}",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == 1  # Only response1
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent_1.identifier)

    @pytest.mark.parametrize(("evidence_rich", "count"), [(True, 1), (False, 1), (None, 2)])
    def test_get_filtered_responses_with_evidence_rich_filters(
        self,
        client,
        consultation_user,
        free_text_question,
        consultation_user_token,
        respondent_1,
        respondent_2,
        evidence_rich,
        count,
    ):
        """Test API endpoint with evidence_rich filtering using AND logic"""
        # Create responses with different theme combinations

        response_1 = ResponseFactory(
            question=free_text_question, respondent=respondent_1, free_text="Response 1"
        )
        response_2 = ResponseFactory(
            question=free_text_question, respondent=respondent_2, free_text="Response 2"
        )

        ResponseAnnotationFactory(response=response_1, evidence_rich=True)
        ResponseAnnotationFactory(response=response_2, evidence_rich=False)

        client.force_login(consultation_user)

        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        response = client.get(
            url + f"?evidenceRich={evidence_rich}",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == count  # Only response1
        assert len(data["all_respondents"]) == 2 if evidence_rich is None else 2
        if evidence_rich is not None:
            assert data["all_respondents"][0]["evidenceRich"] == evidence_rich

    @pytest.mark.parametrize(
        ("sentiments", "count", "expected"),
        [
            ("AGREEMENT,UNCLEAR", 2, ["AGREEMENT", "UNCLEAR"]),
            ("AGREEMENT", 1, ["AGREEMENT"]),
            ("DISAGREEMENT", 0, []),
        ],
    )
    def test_get_filtered_responses_with_sentiment_filters(
        self,
        client,
        consultation_user,
        free_text_question,
        consultation_user_token,
        respondent_1,
        respondent_2,
        sentiments,
        count,
        expected,
    ):
        """Test API endpoint with evidence_rich filtering using AND logic"""
        # Create responses with different theme combinations

        response_1 = ResponseFactory(
            question=free_text_question, respondent=respondent_1, free_text="Response 1"
        )
        response_2 = ResponseFactory(
            question=free_text_question, respondent=respondent_2, free_text="Response 2"
        )

        ResponseAnnotationFactory(
            response=response_1, sentiment=ResponseAnnotation.Sentiment.AGREEMENT
        )
        ResponseAnnotationFactory(
            response=response_2, sentiment=ResponseAnnotation.Sentiment.UNCLEAR
        )

        client.force_login(consultation_user)

        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        response = client.get(
            url + f"?sentimentFilters={sentiments}",
            headers={"Authorization": f"Bearer {consultation_user_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == count  # Only response1
        assert len(data["all_respondents"]) == 2 if sentiments is None else 2

        assert sorted(x["sentiment"] for x in data["all_respondents"]) == expected

    @pytest.mark.parametrize(
        ("is_flagged", "expected_responses"), [(True, 1), (False, 1), (None, 2)]
    )
    def test_get_filtered_response_is_flagged(
        self,
        client,
        consultation_user_token,
        consultation_user,
        free_text_annotation,
        another_annotation,
        is_flagged,
        expected_responses,
    ):
        free_text_annotation.flagged_by.add(consultation_user)
        free_text_annotation.save()

        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "question_pk": free_text_annotation.response.question.id,
            },
        )

        response = client.get(
            url + f"?is_flagged={is_flagged}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )

        assert response.status_code == 200
        assert response.json()["respondents_total"] == 2
        assert response.json()["filtered_total"] == expected_responses
        if expected_responses == 1:
            assert response.json()["all_respondents"][0]["is_flagged"] == is_flagged

    @pytest.mark.parametrize(
        ("chosen_options", "expected_responses"),
        [
            (["red", "blue"], 2),
            (["red"], 2),
            (["blue"], 1),
            (["not-a-real-answer"], 2),
            ([], 2),
        ],
    )
    def test_get_filtered_response_chosen_options(
        self,
        client,
        consultation_user_token,
        consultation_user,
        multi_choice_responses,
        multi_choice_question,
        chosen_options,
        expected_responses,
    ):
        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": multi_choice_question.consultation.id,
                "question_pk": multi_choice_question.id,
            },
        )

        _chosen_options = multi_choice_question.multichoiceanswer_set.filter(
            question=multi_choice_question, text__in=chosen_options
        )

        chosen_options_query = ",".join(str(x.pk) for x in _chosen_options)

        response = client.get(
            url + f"?multiple_choice_answer={chosen_options_query}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )

        assert response.status_code == 200
        assert response.json()["respondents_total"] == 2
        assert response.json()["filtered_total"] == expected_responses

    @pytest.mark.parametrize("is_flagged", [True, False])
    def test_get_responses_with_is_flagged(
        self, client, consultation_user, consultation_user_token, free_text_annotation, is_flagged
    ):
        if is_flagged:
            free_text_annotation.flagged_by.add(consultation_user)
            free_text_annotation.save()

        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "question_pk": free_text_annotation.response.question.id,
                "pk": free_text_annotation.response.id,
            },
        )
        response = client.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_flagged"] == is_flagged


@pytest.mark.django_db
class TestQuestionInformationAPIView:
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
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
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
            headers={
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["question_text"] == multi_choice_question.text
        assert data["total_responses"] == 2
        answer_counts = {x["text"]: x["response_count"] for x in data["multiple_choice_answer"]}
        assert answer_counts == {"blue": 1, "green": 0, "red": 2}


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
        ],
    )
    def test_user_without_dashboard_access_denied(
        self, client, free_text_question, non_dashboard_user, endpoint_name
    ):
        """Test that users without dashboard access cannot access any API endpoint"""
        client.force_login(non_dashboard_user)
        url = build_url(endpoint_name, free_text_question)
        response = client.get(url)
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
        ],
    )
    def test_user_without_consultation_access_denied(
        self, client, free_text_question, user_without_consultation_access, endpoint_name
    ):
        """Test that users without consultation access cannot access any API endpoint"""
        client.force_login(user_without_consultation_access)
        url = build_url(endpoint_name, free_text_question)
        response = client.get(url)
        assert response.status_code == 403

    def test_patch_response_human_reviewed(
        self, client, consultation_user, consultation_user_token, free_text_annotation
    ):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "question_pk": free_text_annotation.response.question.id,
                "pk": free_text_annotation.response.id,
            },
        )

        assert free_text_annotation.human_reviewed is False
        assert free_text_annotation.reviewed_by is None
        assert free_text_annotation.reviewed_at is None

        response = client.patch(
            url,
            data='{"human_reviewed": true}',
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        assert response.json()["human_reviewed"] is True
        free_text_annotation.refresh_from_db()
        assert free_text_annotation.human_reviewed is True

        # Verify version history captures the change from True to False using django-simple-history
        history = free_text_annotation.history.all().order_by("history_date")
        assert history.count() == 2

        # The first version should have human_reviewed=False
        assert history.first().human_reviewed is False
        assert history.first().reviewed_by is None
        assert history.first().reviewed_at is None

        # latest should have human_reviewed=True
        assert history.last().human_reviewed is True
        assert history.last().reviewed_by == consultation_user
        assert isinstance(history.last().reviewed_at, datetime)

    def test_patch_response_sentiment(self, client, consultation_user_token, free_text_annotation):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "question_pk": free_text_annotation.response.question.id,
                "pk": free_text_annotation.response.id,
            },
        )

        assert free_text_annotation.evidence_rich is True

        response = client.patch(
            url,
            data='{"sentiment": "AGREEMENT"}',
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        assert response.json()["sentiment"] == "AGREEMENT"
        free_text_annotation.refresh_from_db()
        assert free_text_annotation.sentiment == "AGREEMENT"

        # Verify version history captures the change from True to False using django-simple-history
        history = free_text_annotation.history.all().order_by("history_date")
        assert history.count() == 2

        # The first version should have sentiment=null, latest should have sentiment="AGREEMENT"
        assert history.first().sentiment is None  # Initial state
        assert history.last().sentiment == "AGREEMENT"  # Final state after PATCH

    def test_patch_response_evidence_rich(
        self, client, consultation_user_token, free_text_annotation
    ):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "question_pk": free_text_annotation.response.question.id,
                "pk": free_text_annotation.response.id,
            },
        )

        assert free_text_annotation.evidence_rich is True

        response = client.patch(
            url,
            data='{"evidenceRich": false}',
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        assert response.json()["evidenceRich"] is False
        free_text_annotation.refresh_from_db()
        assert free_text_annotation.evidence_rich is False

        # Verify version history captures the change from True to False using django-simple-history
        history = free_text_annotation.history.all().order_by("history_date")
        assert history.count() == 2

        # The first version should have evidence_rich=True, latest should have evidence_rich=False
        assert history.first().evidence_rich is True  # Initial state
        assert history.last().evidence_rich is False  # Final state after PATCH

    def test_patch_response_themes(
        self,
        client,
        consultation_user,
        consultation_user_token,
        free_text_annotation,
        alternative_theme,
        ai_assigned_theme,
    ):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "question_pk": free_text_annotation.response.question.id,
                "pk": free_text_annotation.response.id,
            },
        )

        assert list(free_text_annotation.themes.values_list("key", flat=True)) == [
            "AI assigned theme A",
            "Human assigned theme B",
        ]

        response = client.patch(
            url,
            data=json.dumps({"themes": [{"id": str(alternative_theme.id)}]}),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200, response.json()
        assert [(x["assigned_by"], x["key"]) for x in response.json()["themes"]] == [
            ("AI", "AI assigned theme A"),
            (consultation_user.email, "Human assigned theme C"),
        ]

        # check that there are two versions of the ResponseAnnotation
        assert free_text_annotation.history.count() == 2

        # get history of the ResponseAnnotation
        history = ResponseAnnotationTheme.history.filter(
            response_annotation=free_text_annotation
        ).order_by("history_date")
        assert history.count() == 4

        # check all stages of history
        # 0. add initial theme AI assigned theme A and....
        assert history[0].history_type == "+"
        assert history[0].theme.key == "AI assigned theme A"
        assert history[0].assigned_by is None

        # 1. ...Human assigned theme B
        assert history[1].history_type == "+"
        assert history[1].theme.key == "Human assigned theme B"
        assert history[1].assigned_by.email == consultation_user.email

        # 2. remove initial Human assigned theme B
        assert history[2].history_type == "-"
        assert history[2].theme.key == "Human assigned theme B"
        assert history[2].assigned_by.email == consultation_user.email

        # 3. add new Human assigned theme C
        assert history[3].history_type == "+"
        assert history[3].theme.key == "Human assigned theme C"
        assert history[3].assigned_by == consultation_user

        assert list(free_text_annotation.get_original_ai_themes()) == [ai_assigned_theme]

    def test_patch_response_themes_invalid(
        self, client, consultation_user_token, free_text_annotation
    ):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "question_pk": free_text_annotation.response.question.id,
                "pk": free_text_annotation.response.id,
            },
        )

        fake_uuid = str(uuid4())

        response = client.patch(
            url,
            data=json.dumps({"themes": [{"id": fake_uuid}]}),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 400
        assert response.json() == {
            "themes": [[f'Invalid pk "{fake_uuid}" - object does not exist.']]
        }

    @pytest.mark.parametrize("is_flagged", [True, False])
    def test_patch_response_flags(
        self,
        client,
        consultation_user_token,
        consultation_user,
        free_text_annotation,
        is_flagged,
    ):
        url = reverse(
            "response-toggle-flag",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "question_pk": free_text_annotation.response.question.id,
                "pk": free_text_annotation.response.id,
            },
        )

        if is_flagged:
            free_text_annotation.flagged_by.add(consultation_user)

        assert free_text_annotation.flagged_by.contains(consultation_user) == is_flagged

        response = client.patch(
            url,
            data="",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {consultation_user_token}",
            },
        )
        assert response.status_code == 200
        free_text_annotation.refresh_from_db()
        # check that the state has changed
        assert free_text_annotation.flagged_by.contains(consultation_user) != is_flagged


@pytest.mark.django_db
class TestAPIViewErrorHandling:
    """Test error handling across API views"""

    def test_nonexistent_consultation(self, client, consultation_user):
        """Test API endpoints with non-existent consultation"""
        client.force_login(consultation_user)
        url = reverse("consultations-demographic-options", kwargs={"pk": uuid4()})
        response = client.get(url)
        assert response.status_code == 404  # NOT FOUND


@pytest.mark.django_db
def test_consultations_list(client, consultation_user, multi_choice_question):
    client.force_login(consultation_user)
    url = reverse("consultations-list")
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_consultations_list_filter_by_slug(client, consultation_user, multi_choice_question):
    """Test that consultations can be filtered by slug"""
    client.force_login(consultation_user)
    consultation = multi_choice_question.consultation

    # Test filtering by slug
    url = reverse("consultations-list")
    response = client.get(url, {"slug": consultation.slug})
    assert response.status_code == 200

    data = response.json()
    results = data.get("results", data)  # Handle paginated/non-paginated responses

    # Should return exactly one consultation
    assert len(results) == 1
    assert results[0]["slug"] == consultation.slug
    assert results[0]["title"] == consultation.title


@pytest.mark.django_db
def test_consultations_list_filter_by_nonexistent_slug(client, consultation_user):
    """Test that filtering by non-existent slug returns empty results"""
    client.force_login(consultation_user)

    url = reverse("consultations-list")
    response = client.get(url, {"slug": "nonexistent-slug"})
    assert response.status_code == 200

    data = response.json()
    results = data.get("results", data)  # Handle paginated/non-paginated responses

    # Should return empty list
    assert len(results) == 0


@pytest.mark.django_db
def test_multi_choice_answer_count(
    client, consultation_user, multi_choice_question, multi_choice_responses
):
    client.force_login(consultation_user)
    url = reverse(
        "question-multi-choice-response-count",
        kwargs={
            "consultation_pk": multi_choice_question.consultation.pk,
            "pk": multi_choice_question.pk,
        },
    )
    response = client.get(url)
    assert response.status_code == 200

    def sort_by_answer(payload):
        return sorted(payload, key=lambda x: x["answer"])

    expected = [{"answer": "blue", "response_count": 1}, {"answer": "red", "response_count": 2}]
    assert sort_by_answer(response.json()) == sort_by_answer(expected)


@pytest.mark.django_db
@pytest.mark.parametrize("has_free_text", [True, False, ""])
def test_filter(client, consultation_user, consultation, has_free_text):
    """Test filtering questions by has_free_text"""

    # Create questions with different free text settings
    _free_text_question = QuestionFactory(
        consultation=consultation, has_free_text=True, text="Free text question"
    )
    _multi_choice_question = QuestionFactory(
        consultation=consultation, has_free_text=False, text="Multi choice question"
    )

    client.force_login(consultation_user)
    url = reverse("question-list", kwargs={"consultation_pk": consultation.id})

    # Filter by has_free_text=True
    response = client.get(url, {"has_free_text": has_free_text})
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
