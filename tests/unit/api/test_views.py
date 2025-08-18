from uuid import uuid4

import orjson
import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.factories import (
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    UserFactory,
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
        data = response.json()
        assert "demographic_options" in data
        assert data["demographic_options"] == {}

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
        assert "demographic_options" in data
        options = data["demographic_options"]

        assert set(options["individual"]) == {"False", "True"}
        assert set(options["region"]) == {"north", "south"}
        assert set(options["age"]) == {"25", "35", "45"}

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
            "question-demographic-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
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
            "question-demographic-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
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
            demographics={"individual": "True", "region": "north"},
        )
        respondent2 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": "False", "region": "south"},
        )

        ResponseFactory(question=free_text_question, respondent=respondent1)
        ResponseFactory(question=free_text_question, respondent=respondent2)

        client.force_login(consultation_user)
        url = reverse(
            "question-demographic-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )

        # Filter by individual=true
        response = client.get(url + "?demoFilters=individual:True")

        assert response.status_code == 200
        data = response.json()

        # Should only include data from individual=True respondent
        aggregations = data["demographic_aggregations"]
        assert aggregations["individual"]["True"] == 1
        assert aggregations["region"]["north"] == 1
        # Should not have data from individual=False respondent
        assert "False" not in aggregations["individual"]
        assert "south" not in aggregations["region"]

    def test_invalid_filter_parameters(self, client, consultation_user, free_text_question):
        """Test API endpoint handles invalid filter parameters"""
        client.force_login(consultation_user)
        url = reverse(
            "question-demographic-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )

        # Test invalid search mode
        response = client.get(url + "?searchMode=invalid")
        assert response.status_code == 400


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
        self, client, consultation_user, free_text_question, theme, theme2
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
            "question-theme-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "theme_aggregations" in data
        assert data["theme_aggregations"] == {}

    def test_get_theme_aggregations_with_responses(
        self, client, consultation_user, free_text_question, theme, theme2
    ):
        """Test API endpoint returns theme aggregations correctly"""
        # Create respondents and responses
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)

        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        # Create annotations with themes
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme])

        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme, theme2])

        client.force_login(consultation_user)
        url = reverse(
            "question-theme-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "theme_aggregations" in data

        aggregations = data["theme_aggregations"]
        assert aggregations[str(theme.id)] == 2  # Theme A appears in 2 responses
        assert aggregations[str(theme2.id)] == 1  # Theme B appears in 1 response

    def test_get_theme_aggregations_with_filters(
        self, client, consultation_user, free_text_question, theme, theme2
    ):
        """Test API endpoint applies theme filtering correctly"""
        # Create responses with different theme combinations
        respondent1 = RespondentFactory(consultation=free_text_question.consultation)
        respondent2 = RespondentFactory(consultation=free_text_question.consultation)

        response1 = ResponseFactory(question=free_text_question, respondent=respondent1)
        response2 = ResponseFactory(question=free_text_question, respondent=respondent2)

        # Response 1: has theme1 and theme2
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme, theme2])

        # Response 2: has only theme1
        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme])

        client.force_login(consultation_user)
        url = reverse(
            "question-theme-aggregations",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )

        # Filter by theme1 AND theme2 - should only return response1
        response = client.get(url + f"?themeFilters={theme.id},{theme2.id}")

        assert response.status_code == 200
        data = response.json()

        # Should only show counts from responses that have BOTH themes
        aggregations = data["theme_aggregations"]
        assert aggregations[str(theme.id)] == 1  # Only response1 has both themes
        assert aggregations[str(theme2.id)] == 1  # Only response1 has both themes


@pytest.mark.django_db
class TestFilteredResponsesAPIView:
    def test_get_filtered_responses_basic(self, client, consultation_user, free_text_question):
        """Test API endpoint returns filtered responses correctly"""
        # Create test data
        respondent = RespondentFactory(
            consultation=free_text_question.consultation, demographics={"individual": "True"}
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
        assert respondent_data["demographic_data"] == {"individual": "True"}

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
            demographics={"individual": "True", "region": "north"},
        )
        respondent2 = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": "False", "region": "south"},
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
        response = client.get(url + "?demoFilters=individual:True")

        assert response.status_code == 200

        data = orjson.loads(response.content)

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == 1  # Filtered to individuals only
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_get_filtered_responses_with_theme_filters(
        self, client, consultation_user, free_text_question, theme, theme2
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
        annotation1.add_original_ai_themes([theme, theme2])

        # Response 2: has only theme
        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme])

        # Response 3: has only theme2
        annotation3 = ResponseAnnotationFactoryNoThemes(response=response3)
        annotation3.add_original_ai_themes([theme2])

        client.force_login(consultation_user)
        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        # Filter by theme AND theme2 - should only return response1
        response = client.get(url + f"?themeFilters={theme.id},{theme2.id}")

        assert response.status_code == 200

        data = orjson.loads(response.content)

        # assert data["respondents_total"] == 3  # Total respondents
        assert data["filtered_total"] == 1  # Only response1 has both themes
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_get_filtered_responses_invalid_parameters(
        self, client, consultation_user, free_text_question
    ):
        """Test API endpoint handles invalid parameters"""
        client.force_login(consultation_user)
        url = reverse(
            "response-list",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "question_pk": free_text_question.id,
            },
        )

        # Test invalid page_size (too large)
        response = client.get(url + "?page_size=200")
        assert response.status_code == 400

        # Test invalid page number
        response = client.get(url + "?page=0")
        assert response.status_code == 400


@pytest.mark.django_db
class TestQuestionInformationAPIView:
    def test_get_question_information(self, client, consultation_user, free_text_question):
        """Test API endpoint returns question information correctly"""
        # Add a known response count with free text
        for i in range(3):
            respondent = RespondentFactory(consultation=free_text_question.consultation)
            ResponseFactory(
                question=free_text_question, respondent=respondent, free_text=f"Response {i}"
            )

        # Update the total_responses count
        free_text_question.update_total_responses()

        client.force_login(consultation_user)
        url = reverse(
            "question-detail",
            kwargs={
                "consultation_pk": free_text_question.consultation.id,
                "pk": free_text_question.id,
            },
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        assert "question_text" in data
        assert "total_responses" in data
        assert data["question_text"] == free_text_question.text
        assert data["total_responses"] == 3


@pytest.mark.django_db
class TestAPIViewPermissions:
    """Test permissions across all API views"""

    @pytest.fixture()
    def user_without_dashboard_access(self):
        """User without dashboard access"""
        return UserFactory()

    @pytest.fixture()
    def user_without_consultation_access(self):
        """User with dashboard access but not consultation access"""
        user = UserFactory()
        dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
        user.groups.add(dash_access)
        user.save()
        return user

    @pytest.mark.parametrize(
        "endpoint_name",
        [
            "consultations-demographic-options",
            "question-demographic-aggregations",
            "question-theme-information",
            "question-theme-aggregations",
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
            "question-demographic-aggregations",
            "question-theme-information",
            "question-theme-aggregations",
            "response-list",
            "question-detail",
        ],
    )
    def test_user_without_dashboard_access_denied(
        self, client, free_text_question, user_without_dashboard_access, endpoint_name
    ):
        """Test that users without dashboard access cannot access any API endpoint"""
        client.force_login(user_without_dashboard_access)
        url = build_url(endpoint_name, free_text_question)
        response = client.get(url)
        assert response.status_code == 403

    @pytest.mark.parametrize(
        "endpoint_name",
        [
            "consultations-detail",
            "consultations-demographic-options",
            "question-demographic-aggregations",
            "question-theme-information",
            "question-theme-aggregations",
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
