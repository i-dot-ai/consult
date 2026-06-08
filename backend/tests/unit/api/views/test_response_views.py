from datetime import datetime
from uuid import uuid4

import orjson
import pytest
from django.urls import reverse

from consultations.api.views.response import MAX_BULK_MARK_READ
from consultations.models import ResponseAnnotation, ResponseAnnotationTheme, ResponseReadBy
from factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
)


@pytest.mark.django_db
class TestResponseViewSet:
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
        - 1 query to count filtered responses
        - 1 query to get responses with related data (includes is_read annotation)
        - 1 query to prefetch multiple choice answers
        - 1 query to prefetch demographic data
        """
        with django_assert_num_queries(6):
            response = client.get(
                url,
                query_params={"question_id": free_text_question.id},
                headers={"Authorization": f"Bearer {staff_user_token}"},
            )

        assert response.status_code == 200

        # Parse the response
        data = orjson.loads(response.content)

        assert len(data["all_respondents"]) == 2
        assert data["total_count"] == 2

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
        """Test cursor-based pagination returns the correct page and a usable next cursor"""
        for _ in range(5):
            respondent = RespondentFactory(consultation=free_text_question.consultation)
            ResponseFactory(question=free_text_question, respondent=respondent)

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )
        auth = {"Authorization": f"Bearer {staff_user_token}"}

        # First page — no cursor
        page1 = client.get(
            url,
            query_params={"page_size": 2, "question_id": free_text_question.id},
            headers=auth,
        )
        assert page1.status_code == 200
        data1 = orjson.loads(page1.content)
        assert len(data1["all_respondents"]) == 2
        assert data1["has_more_pages"] is True
        assert data1["total_count"] == 5
        assert data1["next_cursor"] is not None

        # Second page — use the cursor from page 1
        page2 = client.get(
            url,
            query_params={
                "page_size": 2,
                "question_id": free_text_question.id,
                "cursor": data1["next_cursor"],
            },
            headers=auth,
        )
        assert page2.status_code == 200
        data2 = orjson.loads(page2.content)
        assert len(data2["all_respondents"]) == 2
        assert data2["has_more_pages"] is True
        # total_count is omitted on subsequent pages to avoid an extra COUNT query
        assert "total_count" not in data2
        # No overlap between pages
        page1_ids = {response["id"] for response in data1["all_respondents"]}
        page2_ids = {response["id"] for response in data2["all_respondents"]}
        assert page1_ids.isdisjoint(page2_ids)

    def test_total_count_returned_on_first_page_only(
        self, client, staff_user_token, free_text_question
    ):
        """total_count is included on page 1 for accurate pagination display, omitted on subsequent pages."""
        for i in range(5):
            respondent = RespondentFactory(consultation=free_text_question.consultation)
            ResponseFactory(question=free_text_question, respondent=respondent)

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        # First load (no cursor) includes total_count
        response = client.get(
            url,
            query_params={"page_size": 2, "question_id": free_text_question.id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        data = orjson.loads(response.content)
        assert data["total_count"] == 5
        assert data["has_more_pages"]
        assert data["next_cursor"] is not None

        # Subsequent load (with cursor) omits total_count
        response = client.get(
            url,
            query_params={
                "page_size": 2,
                "cursor": data["next_cursor"],
                "question_id": free_text_question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        data = orjson.loads(response.content)
        assert "total_count" not in data

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

        assert data["total_count"] == 1  # Filtered to individuals only
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
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme_a, theme_b])

        # Response 2: has only theme
        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme_a])

        # Response 3: has only theme2
        annotation3 = ResponseAnnotationFactoryNoThemes(response=response3)
        annotation3.add_original_ai_themes([theme_b])

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

        assert data["total_count"] == 1  # Only response1 has both themes
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

        assert data["total_count"] == 1  # Only response1
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

        ResponseAnnotationFactory(response=response_1, evidence_rich=True)
        ResponseAnnotationFactory(response=response_2, evidence_rich=False)

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

        assert data["total_count"] == count  # Only response1
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

        ResponseAnnotationFactory(
            response=response_1, sentiment=ResponseAnnotation.Sentiment.AGREEMENT
        )
        ResponseAnnotationFactory(
            response=response_2, sentiment=ResponseAnnotation.Sentiment.UNCLEAR
        )

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

        assert data["total_count"] == count  # Only response1
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
            kwargs={"consultation_pk": free_text_annotation.response.question.consultation.id},
        )

        response = client.get(
            url,
            query_params={
                "is_flagged": is_flagged,
                "question_id": free_text_annotation.response.question.id,
            },
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert response.json()["total_count"] == expected_responses
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
        assert response.json()["total_count"] == expected_responses

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
            human_reviewed_annotation.flagged_by.add(staff_user)
            human_reviewed_annotation.save()

        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": human_reviewed_annotation.response.question.consultation.id,
                "pk": human_reviewed_annotation.response.id,
            },
        )
        response = client.get(
            url,
            query_params={"question_id": human_reviewed_annotation.response.question.id},
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
        assert response.json()["total_count"] == 1
        assert response.json()["all_respondents"][0]["id"] == str(response_1.id)
        assert response.json()["all_respondents"][0]["respondent_id"] == str(respondent_1.id)

    def test_question_responses_excludes_null_free_text(
        self, client, staff_user_token, free_text_question
    ):
        """Responses listed under a question should exclude those with no free text."""
        from consultations.models import Response

        respondent_with_text = RespondentFactory(consultation=free_text_question.consultation)
        respondent_no_text = RespondentFactory(consultation=free_text_question.consultation)
        response_with_text = Response.objects.create(
            question=free_text_question, respondent=respondent_with_text, free_text="some text"
        )
        Response.objects.create(
            question=free_text_question, respondent=respondent_no_text, free_text=None
        )

        # Nested under question — should only return the response with free text
        url = reverse(
            "question-response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )
        response = client.get(url, headers={"Authorization": f"Bearer {staff_user_token}"})

        assert response.status_code == 200
        data = response.json()["all_respondents"]
        assert len(data) == 1
        assert data[0]["id"] == str(response_with_text.id)

    def test_consultation_responses_includes_null_free_text(
        self, client, staff_user_token, free_text_question
    ):
        """Responses listed at consultation level (e.g. respondent detail) include all responses."""
        from consultations.models import Response

        respondent = RespondentFactory(consultation=free_text_question.consultation)
        Response.objects.create(
            question=free_text_question, respondent=respondent, free_text="some text"
        )
        Response.objects.create(question=free_text_question, respondent=respondent, free_text=None)

        url = reverse(
            "response-list",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )
        response = client.get(
            url,
            query_params={"respondent_id": respondent.id},
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert response.status_code == 200
        assert len(response.json()["all_respondents"]) == 2

    def test_patch_response_human_reviewed(
        self, client, staff_user, staff_user_token, free_text_annotation
    ):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "pk": free_text_annotation.response.id,
            },
        )

        assert free_text_annotation.human_reviewed is False
        assert free_text_annotation.reviewed_by is None
        assert free_text_annotation.reviewed_at is None

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
        assert history.count() == 2

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
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "pk": free_text_annotation.response.id,
            },
        )

        assert free_text_annotation.evidence_rich is True

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
        assert history.count() == 2

        # The first version should have sentiment=null, latest should have sentiment="AGREEMENT"
        assert history.first().sentiment is None  # Initial state
        assert history.last().sentiment == "AGREEMENT"  # Final state after PATCH

    def test_patch_response_evidence_rich(self, client, staff_user_token, free_text_annotation):
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "pk": free_text_annotation.response.id,
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
        assert history.count() == 2

        # The first version should have evidence_rich=True, latest should have evidence_rich=False
        assert history.first().evidence_rich is True  # Initial state
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
        url = reverse(
            "response-detail",
            kwargs={
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "pk": free_text_annotation.response.id,
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
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "pk": free_text_annotation.response.id,
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
                "consultation_pk": free_text_annotation.response.question.consultation.id,
                "pk": free_text_annotation.response.id,
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
        assert data["total_count"] == 1

        # Verify respondent data structure
        respondent = data["all_respondents"][0]
        assert respondent["identifier"] == str(respondent1.identifier)
        assert respondent["free_text_answer_text"] == response1.free_text

    def test_get_themes_for_response(self, client, staff_user_token, free_text_question):
        """Test API endpoint returns themes for a specific response"""
        # Create test response
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response_obj = ResponseFactory(question=free_text_question, respondent=respondent)

        # Create annotation with themes
        _ = ResponseAnnotationFactoryNoThemes(response=response_obj)

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
        annotation = ResponseAnnotationFactoryNoThemes(response=response_obj)
        annotation.add_original_ai_themes([theme_a])

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

    def test_get_themes_creates_annotation_if_not_exists(
        self, client, staff_user_token, free_text_question
    ):
        """Test API endpoint creates annotation if it doesn't exist"""
        # Create test response without annotation
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response_obj = ResponseFactory(question=free_text_question, respondent=respondent)

        # Verify no annotation exists initially
        assert not ResponseAnnotation.objects.filter(response=response_obj).exists()

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

        # Verify annotation was created
        assert ResponseAnnotation.objects.filter(response=response_obj).exists()

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

    def test_mark_read_bulk_marks_all_responses(
        self, client, staff_user, staff_user_token, free_text_question
    ):
        """Bulk endpoint marks every supplied response as read in a single request."""
        responses = [ResponseFactory(question=free_text_question) for _ in range(3)]

        url = reverse(
            "response-mark-read-bulk",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        api_response = client.post(
            url,
            data={"response_ids": [str(response.id) for response in responses]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert api_response.status_code == 200
        for response in responses:
            assert response.is_read_by(staff_user)

    def test_mark_read_bulk_is_idempotent(
        self, client, staff_user, staff_user_token, free_text_question
    ):
        """Re-sending already-read responses does not error or create duplicate records."""
        response = ResponseFactory(question=free_text_question)
        response.mark_as_read_by(staff_user)

        url = reverse(
            "response-mark-read-bulk",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        api_response = client.post(
            url,
            data={"response_ids": [str(response.id)]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert api_response.status_code == 200
        assert ResponseReadBy.objects.filter(response=response, user=staff_user).count() == 1

    def test_mark_read_bulk_ignores_responses_outside_consultation(
        self, client, staff_user, staff_user_token, free_text_question
    ):
        """Responses belonging to another consultation are not marked, even if their ID is sent."""
        in_scope = ResponseFactory(question=free_text_question)

        other_consultation = ConsultationFactory(title="Other", code="other-consultation")
        other_question = QuestionFactory(consultation=other_consultation)
        out_of_scope = ResponseFactory(question=other_question)

        url = reverse(
            "response-mark-read-bulk",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        api_response = client.post(
            url,
            data={"response_ids": [str(in_scope.id), str(out_of_scope.id)]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert api_response.status_code == 200
        assert in_scope.is_read_by(staff_user)
        assert not out_of_scope.is_read_by(staff_user)

    def test_mark_read_bulk_rejects_empty_payload(
        self, client, staff_user_token, free_text_question
    ):
        """An empty or missing response_ids list is rejected with a 400."""
        url = reverse(
            "response-mark-read-bulk",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        empty_response = client.post(
            url,
            data={"response_ids": []},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )
        assert empty_response.status_code == 400

    def test_mark_read_bulk_skips_invalid_uuids(
        self, client, staff_user, staff_user_token, free_text_question
    ):
        """Non-UUID values are skipped without erroring; valid IDs are still marked."""
        valid_response = ResponseFactory(question=free_text_question)

        url = reverse(
            "response-mark-read-bulk",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        api_response = client.post(
            url,
            data={"response_ids": ["not-a-uuid", str(valid_response.id)]},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert api_response.status_code == 200
        assert valid_response.is_read_by(staff_user)

    def test_mark_read_bulk_rejects_payload_over_limit(
        self, client, staff_user_token, free_text_question
    ):
        """A payload exceeding the per-request cap is rejected with a 400."""
        too_many_ids = [str(uuid4()) for _ in range(MAX_BULK_MARK_READ + 1)]

        url = reverse(
            "response-mark-read-bulk",
            kwargs={"consultation_pk": free_text_question.consultation.id},
        )

        api_response = client.post(
            url,
            data={"response_ids": too_many_ids},
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert api_response.status_code == 400

    def test_mark_read_bulk_nested_under_question_scopes_to_that_question(
        self, client, staff_user, staff_user_token, consultation
    ):
        """When nested under a question, only that question's responses are marked."""
        question_in_scope = QuestionFactory(consultation=consultation, number=1)
        question_other = QuestionFactory(consultation=consultation, number=2)

        response_in_scope = ResponseFactory(question=question_in_scope)
        response_other_question = ResponseFactory(question=question_other)

        url = reverse(
            "question-response-mark-read-bulk",
            kwargs={
                "consultation_pk": consultation.id,
                "question_pk": question_in_scope.id,
            },
        )

        api_response = client.post(
            url,
            data={
                "response_ids": [
                    str(response_in_scope.id),
                    str(response_other_question.id),
                ]
            },
            content_type="application/json",
            headers={"Authorization": f"Bearer {staff_user_token}"},
        )

        assert api_response.status_code == 200
        assert response_in_scope.is_read_by(staff_user)
        assert not response_other_question.is_read_by(staff_user)
