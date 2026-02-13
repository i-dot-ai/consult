from datetime import datetime
from unittest.mock import patch
from uuid import uuid4

import orjson
import pytest
from django.urls import reverse

from consultations.models import Response, ResponseAnnotationTheme
from factories import (
    RespondentFactory,
    ResponseFactory,
)


@pytest.mark.django_db
class TestResponseViewSet:
    def test_get_demographic_aggregations_empty(self, client, staff_user_token, free_text_question):
        """Test API endpoint returns empty aggregations when no data exists"""
        url = reverse(
            "response-demographic-aggregations",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            query_params={"question_id": free_text_question.id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "demographic_aggregations" in data
        assert data["demographic_aggregations"] == {}

    def test_get_demographic_aggregations_with_data(
        self, client, staff_user_token, free_text_question
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

        url = reverse(
            "response-demographic-aggregations",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            query_params={"question_id": free_text_question.id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

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
        self,
        client,
        staff_user_token,
        free_text_question,
        individual_demographic,
        northern_demographic,
        group_demographic,
        southern_demographic,
    ):
        """Test API endpoint applies demographic filters correctly"""
        # Create respondents with different demographics

        respondent1 = RespondentFactory(
            consultation=free_text_question.consultation,
        )
        respondent1.demographics.set([individual_demographic, northern_demographic])

        respondent2 = RespondentFactory(
            consultation=free_text_question.consultation,
        )
        respondent2.demographics.set([group_demographic, southern_demographic])

        ResponseFactory(question=free_text_question, respondent=respondent1)
        ResponseFactory(question=free_text_question, respondent=respondent2)

        url = reverse(
            "response-demographic-aggregations",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        # Filter by individual=true
        response = client.get(
            url,
            query_params={
                "demographics": individual_demographic.pk,
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only include data from individual=True respondent
        aggregations = data["demographic_aggregations"]
        assert aggregations["individual"]["True"] == 1
        assert aggregations["region"]["north"] == 1
        # Should not have data from individual=False respondent
        assert "False" not in aggregations["individual"]
        assert "south" not in aggregations["region"]

        response = client.get(
            url + "?demoFilters=individual:true&demoFilters=individual:false",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["demographic_aggregations"]["individual"] == {"True": 1, "False": 1}
        assert data["demographic_aggregations"]["region"] == {"north": 1, "south": 1}

    def test_get_theme_aggregations_no_responses(
        self, client, staff_user_token, free_text_question
    ):
        """Test API endpoint returns empty aggregations when no responses exist"""
        url = reverse(
            "response-theme-aggregations",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            query_params={"question_id": free_text_question.id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "theme_aggregations" in data
        assert data["theme_aggregations"] == {}

    def test_get_theme_aggregations_with_responses(
        self, client, staff_user_token, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint returns theme aggregations correctly"""
        # Create respondents and responses
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)

        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        # Create annotations with themes
        response1.add_original_ai_themes([theme_a])

        response2.add_original_ai_themes([theme_a, theme_b])

        url = reverse(
            "response-theme-aggregations",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            query_params={"question_id": free_text_question.id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "theme_aggregations" in data

        aggregations = data["theme_aggregations"]
        assert aggregations[str(theme_a.id)] == 2  # Theme A appears in 2 responses
        assert aggregations[str(theme_b.id)] == 1  # Theme B appears in 1 response

    def test_get_theme_aggregations_with_filters(
        self, client, staff_user_token, free_text_question, theme_a, theme_b
    ):
        """Test API endpoint applies theme filtering correctly"""
        # Create responses with different theme combinations
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)

        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        # Response 1: has theme1 and theme2
        response1.add_original_ai_themes([theme_a, theme_b])

        # Response 2: has only theme1
        response2.add_original_ai_themes([theme_a])

        url = reverse(
            "response-theme-aggregations",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        # Filter by theme1 AND theme2 - should only return response1
        response = client.get(
            url,
            query_params={
                "themeFilters": f"{theme_a.id},{theme_b.id}",
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should only show counts from responses that have BOTH themes
        aggregations = data["theme_aggregations"]
        assert aggregations[str(theme_a.id)] == 1  # Only response1 has both themes
        assert aggregations[str(theme_b.id)] == 1  # Only response1 has both themes

    def test_get_filtered_responses_basic(
        self, client, staff_user_token, free_text_question, django_assert_num_queries
    ):
        """Test API endpoint returns filtered responses correctly"""
        # Create test data
        respondent1 = RespondentFactory(
            consultation=free_text_question.consultation,
            themefinder_id=1,
            demographics={"individual": True},
        )
        respondent2 = RespondentFactory(
            consultation=free_text_question.consultation,
            themefinder_id=2,
            demographics={"individual": False},
        )
        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        """
        Test for no N+1 queries. Regardless of the number of responses, we expect:
        - 1 query to get authentication user for permission checking
        - 1 query to get authentication user for is_flagged annotation
        - 1 query to count respondents
        - 1 query to count filtered responses
        - 1 query to get responses with related data (includes is_read annotation)
        - 1 query to prefetch multiple choice answers
        - 1 query to prefetch demographic data
        - 1 query to prefetch theme data
        """
        with django_assert_num_queries(8):
            response = client.get(
                url,
                query_params={"question_id": free_text_question.id},
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 200

        # Parse the response
        data = orjson.loads(response.content)

        assert len(data["all_respondents"]) == 2
        assert data["respondents_total"] == 2
        assert data["filtered_total"] == 2

        # Verify respondent data structure
        respondents = sorted(data["all_respondents"], key=lambda x: x["identifier"])
        assert respondents[0]["identifier"] == str(respondent1.identifier)
        assert respondents[0]["free_text_answer_text"] == response1.free_text
        assert respondents[0]["demographic_data"] == {"individual": True}
        assert respondents[1]["identifier"] == str(respondent2.identifier)
        assert respondents[1]["free_text_answer_text"] == response2.free_text
        assert respondents[1]["demographic_data"] == {"individual": False}

    def test_get_filtered_responses_with_pagination(
        self, client, staff_user_token, free_text_question
    ):
        """Test API endpoint pagination"""
        # Create multiple respondents
        for i in range(5):
            respondent = RespondentFactory(consultation=free_text_question.consultation)
            ResponseFactory(question=free_text_question, respondent=respondent)

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            query_params={
                "page_size": 2,
                "page": 1,
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

        data = orjson.loads(response.content)

        assert len(data["all_respondents"]) == 2
        assert data["has_more_pages"]
        assert data["filtered_total"] == 5

    def test_get_filtered_responses_with_demographic_filters(
        self,
        client,
        staff_user_token,
        free_text_question,
        individual_demographic,
        northern_demographic,
        group_demographic,
        southern_demographic,
    ):
        """Test API endpoint with demographic filtering"""
        # Create respondents with different demographics
        respondent1 = RespondentFactory(
            consultation=free_text_question.consultation,
        )
        respondent1.demographics.set([individual_demographic, northern_demographic])
        respondent2 = RespondentFactory(
            consultation=free_text_question.consultation,
        )
        respondent2.demographics.set([group_demographic, southern_demographic])

        ResponseFactory(question=free_text_question, respondent=respondent1)
        ResponseFactory(question=free_text_question, respondent=respondent2)

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        # Filter by individual=true
        response = client.get(
            url,
            query_params={
                "demographics": individual_demographic.pk,
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

        data = orjson.loads(response.content)

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == 1  # Filtered to individuals only
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_get_filtered_responses_with_theme_filters(
        self, client, staff_user_token, free_text_question, theme_a, theme_b
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
        response1.add_original_ai_themes([theme_a, theme_b])

        # Response 2: has only theme
        response2.add_original_ai_themes([theme_a])

        # Response 3: has only theme2
        response3.add_original_ai_themes([theme_b])

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        # Filter by theme AND theme2 - should only return response1
        response = client.get(
            url,
            query_params={
                "themeFilters": f"{theme_a.id},{theme_b.id}",
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

        data = orjson.loads(response.content)

        # assert data["respondents_total"] == 3  # Total respondents
        assert data["filtered_total"] == 1  # Only response1 has both themes
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_get_filtered_responses_with_respondent_filters(
        self,
        client,
        staff_user,
        free_text_question,
        staff_user_token,
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

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        # Filter by respondent1 - should only return response1
        response = client.get(
            url,
            query_params={
                "respondent_id": respondent_1.id,
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == 1  # Only response1
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent_1.identifier)

    @pytest.mark.parametrize(("evidence_rich", "count"), [(True, 1), (False, 1), ("", 2)])
    def test_get_filtered_responses_with_evidence_rich_filters(
        self,
        client,
        staff_user,
        free_text_question,
        staff_user_token,
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

        response_1.evidence_rich = True
        response_1.save()

        response_2.evidence_rich = False
        response_2.save()

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        response = client.get(
            url,
            query_params={
                "evidenceRich": evidence_rich,
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == count  # Only response1
        assert len(data["all_respondents"]) == 2 if evidence_rich is None else 2
        if isinstance(evidence_rich, bool):
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
        staff_user,
        free_text_question,
        staff_user_token,
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

        response_1.sentiment = Response.Sentiment.AGREEMENT
        response_1.save()

        response_2.sentiment = Response.Sentiment.UNCLEAR
        response_2.save()

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        response = client.get(
            url,
            query_params={
                "sentimentFilters": sentiments,
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

        data = response.json()

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == count  # Only response1
        assert len(data["all_respondents"]) == 2 if sentiments is None else 2

        assert sorted(x["sentiment"] for x in data["all_respondents"]) == expected

    @pytest.mark.parametrize(("is_flagged", "expected_responses"), [(True, 1), (False, 1), ("", 2)])
    def test_get_filtered_response_is_flagged(
        self,
        client,
        staff_user_token,
        staff_user,
        free_text_annotation,
        human_reviewed_annotation,
        is_flagged,
        expected_responses,
    ):
        free_text_annotation.flagged_by.add(staff_user)
        free_text_annotation.save()

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_annotation.question.consultation.id},
        )

        response = client.get(
            url,
            query_params={
                "is_flagged": is_flagged,
                "question_id": free_text_annotation.question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
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
        staff_user_token,
        staff_user,
        multi_choice_responses,
        multi_choice_question,
        chosen_options,
        expected_responses,
    ):
        url = reverse(
            "response-list",
            kwargs={"consultation_pk": multi_choice_question.consultation.id},
        )

        _chosen_options = multi_choice_question.multichoiceanswer_set.filter(
            question=multi_choice_question, text__in=chosen_options
        )

        chosen_options_query = ",".join(str(x.pk) for x in _chosen_options)

        response = client.get(
            url,
            query_params={
                "multiple_choice_answer": chosen_options_query,
                "question_id": multi_choice_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert response.json()["respondents_total"] == 2
        assert response.json()["filtered_total"] == expected_responses

    @pytest.mark.parametrize(("is_flagged", "is_edited"), [(True, True), (False, False)])
    def test_get_responses_with_is_flagged(
        self,
        client,
        staff_user,
        staff_user_token,
        human_reviewed_annotation,
        is_flagged,
        is_edited,
    ):
        if is_flagged:
            human_reviewed_annotation.is_flagged = True
            human_reviewed_annotation.flagged_by.add(staff_user)
            human_reviewed_annotation.save()

        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": human_reviewed_annotation.question.consultation.id,
                "pk": human_reviewed_annotation.id,
            },
        )
        response = client.get(
            url,
            query_params={"question_id": human_reviewed_annotation.question.id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_flagged"] == is_flagged
        assert data["is_edited"] == is_edited

    def test_get_responses_filtered_by_respondent(
        self,
        client,
        consultation,
        free_text_question,
        respondent_1,
        respondent_2,
        staff_user_token,
    ):
        """
        Given two responses by two different respondents
        when I query by one of the respondent_ids
        I expect only the relevant responses to be returned
        """
        response_1 = ResponseFactory(respondent=respondent_1, question=free_text_question)
        _response_2 = ResponseFactory(respondent=respondent_2, question=free_text_question)

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": consultation.id},
        )

        response = client.get(
            url,
            query_params={
                "respondent_id": respondent_1.id,
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200, response.json()
        assert response.json()["respondents_total"] == 2
        assert response.json()["filtered_total"] == 1
        assert response.json()["all_respondents"][0]["id"] == str(response_1.id)
        assert response.json()["all_respondents"][0]["respondent_id"] == str(respondent_1.id)

    def test_patch_response_human_reviewed(
        self, client, staff_user, staff_user_token, free_text_annotation
    ):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.question.consultation.id,
                "pk": free_text_annotation.id,
            },
        )

        assert free_text_annotation.human_reviewed is False
        assert free_text_annotation.reviewed_by is None
        assert free_text_annotation.reviewed_at is None

        start_count = free_text_annotation.history.count()

        response = client.patch(
            url,
            data={"human_reviewed": True},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["human_reviewed"] is True
        free_text_annotation.refresh_from_db()
        assert free_text_annotation.human_reviewed is True

        # Verify version history captures the change from True to False using django-simple-history
        history = free_text_annotation.history.all().order_by("history_date")
        assert history.count() == start_count + 1

        # The first version should have human_reviewed=False
        assert history.first().human_reviewed is False
        assert history.first().reviewed_by is None
        assert history.first().reviewed_at is None

        # latest should have human_reviewed=True
        assert history.last().human_reviewed is True
        assert history.last().reviewed_by == staff_user
        assert isinstance(history.last().reviewed_at, datetime)

    def test_patch_response_sentiment(self, client, staff_user_token, free_text_annotation):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.question.consultation.id,
                "pk": free_text_annotation.id,
            },
        )

        assert free_text_annotation.evidence_rich is True

        start_count = free_text_annotation.history.count()

        response = client.patch(
            url,
            data={"sentiment": "AGREEMENT"},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200, response.json()
        assert response.json()["sentiment"] == "AGREEMENT"
        free_text_annotation.refresh_from_db()
        assert free_text_annotation.sentiment == "AGREEMENT"
        assert response.json()["is_edited"] is True

        # Verify version history captures the change from True to False using django-simple-history
        history = free_text_annotation.history.all().order_by("history_date")
        assert history.count() == start_count + 1

        # The first version should have sentiment=null, latest should have sentiment="AGREEMENT"
        assert history.first().sentiment is None  # Initial state
        assert history.last().sentiment == "AGREEMENT"  # Final state after PATCH

    def test_patch_response_evidence_rich(self, client, staff_user_token, free_text_annotation):
        start_count = free_text_annotation.history.count()
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.question.consultation.id,
                "pk": free_text_annotation.id,
            },
        )

        assert free_text_annotation.evidence_rich is True

        response = client.patch(
            url,
            data={"evidenceRich": False},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200
        assert response.json()["evidenceRich"] is False
        assert response.json()["is_edited"] is True
        free_text_annotation.refresh_from_db()
        assert free_text_annotation.evidence_rich is False

        # Verify version history captures the change from True to False using django-simple-history
        history = free_text_annotation.history.all().order_by("history_date")
        assert history.count() == start_count + 1

        # The first version should have evidence_rich=True, latest should have evidence_rich=False
        assert list(history.all())[-2].evidence_rich is True  # Initial state
        assert history.last().evidence_rich is False  # Final state after PATCH

    def test_patch_response_themes(
        self,
        client,
        staff_user,
        staff_user_token,
        free_text_annotation,
        alternative_theme,
        ai_assigned_theme,
    ):
        start_count = free_text_annotation.history.count()

        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.question.consultation.id,
                "pk": free_text_annotation.id,
            },
        )

        assert list(free_text_annotation.themes.values_list("key", flat=True)) == [
            "AI assigned theme A",
            "Human assigned theme B",
        ]

        response = client.patch(
            url,
            data={"themes": [{"id": str(ai_assigned_theme.id)}, {"id": str(alternative_theme.id)}]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200, response.json()
        assert [(x["assigned_by"], x["key"]) for x in response.json()["themes"]] == [
            ("AI", "AI assigned theme A"),
            (staff_user.email, "Human assigned theme C"),
        ]

        assert response.json()["is_edited"] is True

        # check that there are two versions of the Response (initial + after theme update)
        assert free_text_annotation.history.count() == start_count + 1

        # get history of the ResponseAnnotationTheme
        history = ResponseAnnotationTheme.history.filter(response=free_text_annotation).order_by(
            "history_date"
        )
        assert history.count() == 4

        # check all stages of history
        # 0. add initial theme AI assigned theme A and....
        assert history[0].history_type == "+"
        assert history[0].theme.key == "AI assigned theme A"
        assert history[0].assigned_by is None

        # 1. ...Human assigned theme B
        assert history[1].history_type == "+"
        assert history[1].theme.key == "Human assigned theme B"
        assert history[1].assigned_by.email == staff_user.email

        # 2. remove initial Human assigned theme B
        assert history[2].history_type == "-"
        assert history[2].theme.key == "Human assigned theme B"
        assert history[2].assigned_by.email == staff_user.email

        # 3. add new Human assigned theme C
        assert history[3].history_type == "+"
        assert history[3].theme.key == "Human assigned theme C"
        assert history[3].assigned_by == staff_user

        assert list(free_text_annotation.get_original_ai_themes()) == [ai_assigned_theme]

    def test_patch_response_themes_invalid(self, client, staff_user_token, free_text_annotation):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.question.consultation.id,
                "pk": free_text_annotation.id,
            },
        )

        fake_uuid = str(uuid4())

        response = client.patch(
            url,
            data={"themes": [{"id": fake_uuid}]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 400
        assert response.json() == {
            "themes": [[f'Invalid pk "{fake_uuid}" - object does not exist.']]
        }

    @pytest.mark.parametrize("is_flagged", [True, False])
    def test_patch_response_flags(
        self,
        client,
        staff_user_token,
        staff_user,
        free_text_annotation,
        is_flagged,
    ):
        url = reverse(
            "response-toggle-flag",
            kwargs={
                "consultation_pk": free_text_annotation.question.consultation.id,
                "pk": free_text_annotation.id,
            },
        )

        if is_flagged:
            free_text_annotation.flagged_by.add(staff_user)

        assert free_text_annotation.flagged_by.contains(staff_user) == is_flagged

        response = client.patch(
            url,
            data="",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert response.status_code == 200

        free_text_annotation.refresh_from_db()
        # check that the state has changed
        assert free_text_annotation.flagged_by.contains(staff_user) != is_flagged
        assert free_text_annotation.is_edited is True

    def test_keyword_search(self, client, staff_user_token, free_text_question):
        """Test API endpoint only returns responses matching keyword search"""
        # Create test data
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)
        response1 = ResponseFactory(
            question=free_text_question, respondent=respondent1, free_text="I love apples"
        )
        ResponseFactory(
            question=free_text_question, respondent=respondent2, free_text="I have no opinion"
        )

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            query_params={
                "question_id": free_text_question.id,
                "searchMode": "keyword",
                "searchValue": "apples",
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

        # Parse the response
        data = orjson.loads(response.content)

        assert len(data["all_respondents"]) == 1
        assert data["respondents_total"] == 2
        assert data["filtered_total"] == 1

        # Verify respondent data structure
        respondent = data["all_respondents"][0]
        assert respondent["identifier"] == str(respondent1.identifier)
        assert respondent["free_text_answer_text"] == response1.free_text

    def test_semantic_search(
        self,
        client,
        staff_user_token,
        embedded_responses,
    ):
        """Test API endpoint returns responses in order of semantic similarity"""
        url = reverse(
            "response-list",
            kwargs={"consultation_pk": embedded_responses["consultation_id"]},
        )

        with patch(
            "consultations.api.filters.embed_text",
            return_value=embedded_responses["search_mode"]["semantic"]["embedding"],
        ):
            response = client.get(
                url,
                query_params={
                    "question_id": embedded_responses["question_id"],
                    "searchMode": "semantic",
                    "searchValue": "public transport",
                },
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 200

        # Parse the response
        data = orjson.loads(response.content)

        assert len(data["all_respondents"]) == 5
        assert data["respondents_total"] == 5
        assert data["filtered_total"] == 5

        # Verify order of responses by semantic similarity to searchValue
        response_texts = [r["free_text_answer_text"] for r in data["all_respondents"]]
        assert response_texts == [
            "We need better buses and trains to connect our neighbourhoods",
            "The local council should really be investing in public transport infrastructure to help reduce carbon emissions",
            "I drive to work every day and fuel costs are rising rapidly",
            "Something must be done about bin collections in my area",
            "The local library needs more funding for children's programs",
        ]

    def test_representative_response_search(
        self, client, staff_user_token, embedded_responses, django_assert_num_queries
    ):
        """Test API endpoint returns representative responses for a theme"""
        url = reverse(
            "response-list",
            kwargs={"consultation_pk": embedded_responses["consultation_id"]},
        )
        theme_name = "Public Transport"
        theme_description = "Local councils should invest in public transport infrastructure"

        with patch(
            "consultations.api.filters.embed_text",
            return_value=embedded_responses["search_mode"]["representative"]["embedding"],
        ):
            """
            Test for no N+1 queries. Regardless of the number of responses, we expect:
            - 1 query to get authentication user for permission checking
            - 1 query to get authentication user for is_flagged annotation
            - 1 query to count respondents
            - 1 query to count filtered responses
            - 1 query to get responses with related data (includes is_read annotation)
            - 1 query to calculate average hybrid_score across responses
            - 1 query to calculate standard deviation of hybrid_score across responses
            - 1 query to prefetch multiple choice answers
            - 1 query to prefetch demographic data
            - 1 query to prefetch theme data
            """
            with django_assert_num_queries(10):
                response = client.get(
                    url,
                    query_params={
                        "question_id": embedded_responses["question_id"],
                        "searchMode": "representative",
                        "searchValue": f"{theme_name} {theme_description}",
                    },
                    headers={"Authorization": f"Bearer {staff_user_token}"},
                )

        assert response.status_code == 200

        # Parse the response
        data = orjson.loads(response.content)

        assert len(data["all_respondents"]) == 1
        assert data["respondents_total"] == 5
        assert data["filtered_total"] == 1

        # Verify which responses are considered representative
        response_texts = [r["free_text_answer_text"] for r in data["all_respondents"]]
        assert response_texts == [
            "The local council should really be investing in public transport infrastructure to help reduce carbon emissions",
        ]

    def test_get_themes_for_response(self, client, staff_user_token, free_text_question):
        """Test API endpoint returns themes for a specific response"""
        # Create test response
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response_obj = ResponseFactory(question=free_text_question, respondent=respondent)

        url = reverse(
            "response-themes",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": response_obj.id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "selected_themes" in data
        assert "all_themes" in data
        assert isinstance(data["selected_themes"], list)
        assert isinstance(data["all_themes"], list)

    @pytest.mark.parametrize("display_ai_selected_themes", [True, False])
    def test_get_themes_for_response_with_selected_themes(
        self,
        client,
        staff_user_token,
        consultation,
        free_text_question,
        theme_a,
        theme_b,
        display_ai_selected_themes,
    ):
        """Test API endpoint returns correct selected and all themes"""
        consultation.display_ai_selected_themes = display_ai_selected_themes
        consultation.save()

        # Create test response
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response_obj = ResponseFactory(question=free_text_question, respondent=respondent)

        # Create annotation with specific themes
        response_obj.add_original_ai_themes([theme_a])

        url = reverse(
            "response-themes",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": response_obj.id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        data = response.json()

        # If display_ai_selected_themes should have theme_a in selected themes
        selected_theme_ids = [theme["id"] for theme in data["selected_themes"]]
        if display_ai_selected_themes:
            assert str(theme_a.id) in selected_theme_ids
        else:
            assert str(theme_a.id) not in selected_theme_ids

        # Should have both themes in all themes
        all_theme_ids = [theme["id"] for theme in data["all_themes"]]
        assert str(theme_a.id) in all_theme_ids
        assert str(theme_b.id) in all_theme_ids

    def test_get_themes_for_nonexistent_response(
        self, client, staff_user_token, free_text_question
    ):
        """Test API endpoint returns 404 for nonexistent response"""
        fake_response_id = "00000000-0000-0000-0000-000000000000"

        url = reverse(
            "response-themes",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": fake_response_id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 404

    def test_get_themes_works_with_null_keys(
        self, client, staff_user_token, free_text_question, theme_c
    ):
        """Test API endpoint works if the underlying them has no key"""
        # Create test response without annotation
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response_obj = ResponseFactory(question=free_text_question, respondent=respondent)

        url = reverse(
            "response-themes",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": response_obj.id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200

    @pytest.mark.parametrize("annotation_exists", [True, False])
    def test_empty_themes_encoding(
        self, client, staff_user_token, free_text_question, respondent_1, annotation_exists
    ):
        """Test API endpoint to ensure that empty themes are always encoded consistently"""
        # Create test response without annotation
        response = ResponseFactory(question=free_text_question, respondent=respondent_1)

        if annotation_exists:
            ResponseAnnotation.objects.create(response=response)

        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
            },
        )

        response = client.get(
            url,
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert response.json()["all_respondents"][0]["themes"] == []
