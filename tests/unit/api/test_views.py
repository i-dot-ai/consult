import orjson
import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory
from django.urls import reverse

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.models import DemographicOption
from consultation_analyser.factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    ThemeFactory,
    UserFactory,
)


@pytest.fixture()
def consultation():
    return ConsultationFactory()


@pytest.fixture()
def question(consultation):
    return QuestionFactory(consultation=consultation, has_free_text=True, has_multiple_choice=False)


@pytest.fixture()
def theme(question):
    return ThemeFactory(question=question, name="Theme A", key="A")


@pytest.fixture()
def theme2(question):
    return ThemeFactory(question=question, name="Theme B", key="B")


@pytest.fixture()
def consultation_user(consultation):
    user = UserFactory()
    dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user.groups.add(dash_access)
    user.save()
    consultation.users.add(user)
    return user


@pytest.fixture()
def request_factory():
    return RequestFactory()


@pytest.mark.django_db
class TestDemographicOptionsAPIView:
    def test_get_demographic_options_empty(self, client, consultation_user, question):
        """Test API endpoint returns empty options when no demographic data exists"""
        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_options",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "demographic_options" in data
        assert data["demographic_options"] == {}

    def test_get_demographic_options_with_data(self, client, consultation_user, question):
        """Test API endpoint returns demographic options correctly"""
        # Create respondents with different demographic data
        RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": True, "region": "north", "age": 25}
        )
        RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": False, "region": "south", "age": 35}
        )
        RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": True, "region": "north", "age": 45}
        )

        # Rebuild demographic options from respondent data
        DemographicOption.rebuild_for_consultation(question.consultation)

        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_options",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "demographic_options" in data
        options = data["demographic_options"]
        
        assert set(options["individual"]) == {"False", "True"}
        assert set(options["region"]) == {"north", "south"}
        assert set(options["age"]) == {"25", "35", "45"}

    def test_permission_required(self, client, question):
        """Test API endpoint requires proper permissions"""
        url = reverse(
            "api_demographic_options",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)
        assert response.status_code == 403

    def test_invalid_consultation_slug(self, client, consultation_user):
        """Test API endpoint with invalid consultation slug"""
        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_options",
            kwargs={"consultation_slug": "invalid", "question_slug": "invalid"}
        )
        response = client.get(url)
        assert response.status_code == 403  # DRF returns 403 for permission denied


@pytest.mark.django_db
class TestDemographicAggregationsAPIView:
    def test_get_demographic_aggregations_empty(self, client, consultation_user, question):
        """Test API endpoint returns empty aggregations when no data exists"""
        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_aggregations",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "demographic_aggregations" in data
        assert data["demographic_aggregations"] == {}

    def test_get_demographic_aggregations_with_data(self, client, consultation_user, question):
        """Test API endpoint returns demographic aggregations correctly"""
        # Create respondents with different demographic data
        respondent1 = RespondentFactory(
            consultation=question.consultation,
            demographics={"gender": "male", "age_group": "25-34", "region": "north"},
        )
        respondent2 = RespondentFactory(
            consultation=question.consultation,
            demographics={"gender": "female", "age_group": "25-34", "region": "south"},
        )
        respondent3 = RespondentFactory(
            consultation=question.consultation,
            demographics={"gender": "male", "age_group": "35-44", "region": "north"},
        )

        # Create responses for each respondent
        ResponseFactory(respondent=respondent1, question=question)
        ResponseFactory(respondent=respondent2, question=question)
        ResponseFactory(respondent=respondent3, question=question)

        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_aggregations",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
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

    def test_get_demographic_aggregations_with_filters(self, client, consultation_user, question):
        """Test API endpoint applies demographic filters correctly"""
        # Create respondents with different demographics
        respondent1 = RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": True, "region": "north"}
        )
        respondent2 = RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": False, "region": "south"}
        )

        ResponseFactory(question=question, respondent=respondent1)
        ResponseFactory(question=question, respondent=respondent2)

        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_aggregations",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
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

    def test_invalid_filter_parameters(self, client, consultation_user, question):
        """Test API endpoint handles invalid filter parameters"""
        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_aggregations",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        
        # Test invalid search mode
        response = client.get(url + "?searchMode=invalid")
        assert response.status_code == 400


@pytest.mark.django_db
class TestThemeInformationAPIView:
    def test_get_theme_information_no_themes(self, client, consultation_user, question):
        """Test API endpoint returns empty themes list when no themes exist"""
        client.force_login(consultation_user)
        url = reverse(
            "api_theme_information",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "themes" in data
        assert data["themes"] == []

    def test_get_theme_information_with_themes(self, client, consultation_user, question, theme, theme2):
        """Test API endpoint returns theme information correctly"""
        client.force_login(consultation_user)
        url = reverse(
            "api_theme_information",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
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
    def test_get_theme_aggregations_no_responses(self, client, consultation_user, question):
        """Test API endpoint returns empty aggregations when no responses exist"""
        client.force_login(consultation_user)
        url = reverse(
            "api_theme_aggregations",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "theme_aggregations" in data
        assert data["theme_aggregations"] == {}

    def test_get_theme_aggregations_with_responses(self, client, consultation_user, question, theme, theme2):
        """Test API endpoint returns theme aggregations correctly"""
        # Create respondents and responses
        respondent1 = RespondentFactory(consultation=question.consultation)
        respondent2 = RespondentFactory(consultation=question.consultation)

        response1 = ResponseFactory(question=question, respondent=respondent1)
        response2 = ResponseFactory(question=question, respondent=respondent2)

        # Create annotations with themes
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme])

        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme, theme2])

        client.force_login(consultation_user)
        url = reverse(
            "api_theme_aggregations",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert "theme_aggregations" in data
        
        aggregations = data["theme_aggregations"]
        assert aggregations[str(theme.id)] == 2  # Theme A appears in 2 responses
        assert aggregations[str(theme2.id)] == 1  # Theme B appears in 1 response

    def test_get_theme_aggregations_with_filters(self, client, consultation_user, question, theme, theme2):
        """Test API endpoint applies theme filtering correctly"""
        # Create responses with different theme combinations
        respondent1 = RespondentFactory(consultation=question.consultation)
        respondent2 = RespondentFactory(consultation=question.consultation)

        response1 = ResponseFactory(question=question, respondent=respondent1)
        response2 = ResponseFactory(question=question, respondent=respondent2)

        # Response 1: has theme1 and theme2
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme, theme2])

        # Response 2: has only theme1
        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme])

        client.force_login(consultation_user)
        url = reverse(
            "api_theme_aggregations",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
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
    def test_get_filtered_responses_basic(self, client, consultation_user, question):
        """Test API endpoint returns filtered responses correctly"""
        # Create test data
        respondent = RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": True}
        )
        ResponseFactory(
            question=question, 
            respondent=respondent, 
            free_text="Test response"
        )

        client.force_login(consultation_user)
        url = reverse(
            "api_filtered_responses",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        
        # Parse the streaming response
        content = b''.join(response.streaming_content)
        data = orjson.loads(content)

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

    def test_get_filtered_responses_with_pagination(self, client, consultation_user, question):
        """Test API endpoint pagination"""
        # Create multiple respondents
        for i in range(5):
            respondent = RespondentFactory(consultation=question.consultation)
            ResponseFactory(question=question, respondent=respondent)

        client.force_login(consultation_user)
        url = reverse(
            "api_filtered_responses",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url + "?page_size=2&page=1")

        assert response.status_code == 200
        
        content = b''.join(response.streaming_content)
        data = orjson.loads(content)

        assert len(data["all_respondents"]) == 2
        assert data["has_more_pages"] is True
        assert data["respondents_total"] == 5

    def test_get_filtered_responses_with_demographic_filters(self, client, consultation_user, question):
        """Test API endpoint with demographic filtering"""
        # Create respondents with different demographics
        respondent1 = RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": True, "region": "north"}
        )
        respondent2 = RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": False, "region": "south"}
        )

        ResponseFactory(question=question, respondent=respondent1)
        ResponseFactory(question=question, respondent=respondent2)

        client.force_login(consultation_user)
        url = reverse(
            "api_filtered_responses",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        
        # Filter by individual=true
        response = client.get(url + "?demoFilters=individual:true")

        assert response.status_code == 200
        
        content = b''.join(response.streaming_content)
        data = orjson.loads(content)

        assert data["respondents_total"] == 2  # Total respondents
        assert data["filtered_total"] == 1  # Filtered to individuals only
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_get_filtered_responses_with_theme_filters(self, client, consultation_user, question, theme, theme2):
        """Test API endpoint with theme filtering using AND logic"""
        # Create responses with different theme combinations
        respondent1 = RespondentFactory(consultation=question.consultation)
        respondent2 = RespondentFactory(consultation=question.consultation)
        respondent3 = RespondentFactory(consultation=question.consultation)

        response1 = ResponseFactory(question=question, respondent=respondent1, free_text="Response 1")
        response2 = ResponseFactory(question=question, respondent=respondent2, free_text="Response 2")
        response3 = ResponseFactory(question=question, respondent=respondent3, free_text="Response 3")

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
            "api_filtered_responses",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        
        # Filter by theme AND theme2 - should only return response1
        response = client.get(url + f"?themeFilters={theme.id},{theme2.id}")

        assert response.status_code == 200
        
        content = b''.join(response.streaming_content)
        data = orjson.loads(content)

        assert data["respondents_total"] == 3  # Total respondents
        assert data["filtered_total"] == 1  # Only response1 has both themes
        assert len(data["all_respondents"]) == 1
        assert data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

    def test_get_filtered_responses_invalid_parameters(self, client, consultation_user, question):
        """Test API endpoint handles invalid parameters"""
        client.force_login(consultation_user)
        url = reverse(
            "api_filtered_responses",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        
        # Test invalid page_size (too large)
        response = client.get(url + "?page_size=200")
        assert response.status_code == 400

        # Test invalid page number
        response = client.get(url + "?page=0")
        assert response.status_code == 400


@pytest.mark.django_db
class TestQuestionInformationAPIView:
    def test_get_question_information(self, client, consultation_user, question):
        """Test API endpoint returns question information correctly"""
        # Add a known response count with free text
        for i in range(3):
            respondent = RespondentFactory(consultation=question.consultation)
            ResponseFactory(question=question, respondent=respondent, free_text=f"Response {i}")
        
        # Update the total_responses count
        question.update_total_responses()

        client.force_login(consultation_user)
        url = reverse(
            "api_question_information",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        
        assert "question_text" in data
        assert "total_responses" in data
        assert data["question_text"] == question.text
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

    @pytest.mark.parametrize("endpoint_name", [
        "api_demographic_options",
        "api_demographic_aggregations", 
        "api_theme_information",
        "api_theme_aggregations",
        "api_filtered_responses",
        "api_question_information"
    ])
    def test_unauthenticated_access_denied(self, client, question, endpoint_name):
        """Test that unauthenticated users cannot access any API endpoint"""
        url = reverse(
            endpoint_name,
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)
        assert response.status_code == 403

    @pytest.mark.parametrize("endpoint_name", [
        "api_demographic_options",
        "api_demographic_aggregations", 
        "api_theme_information",
        "api_theme_aggregations",
        "api_filtered_responses",
        "api_question_information"
    ])
    def test_user_without_dashboard_access_denied(self, client, question, user_without_dashboard_access, endpoint_name):
        """Test that users without dashboard access cannot access any API endpoint"""
        client.force_login(user_without_dashboard_access)
        url = reverse(
            endpoint_name,
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)
        assert response.status_code == 403

    @pytest.mark.parametrize("endpoint_name", [
        "api_demographic_options",
        "api_demographic_aggregations", 
        "api_theme_information",
        "api_theme_aggregations",
        "api_filtered_responses",
        "api_question_information"
    ])
    def test_user_without_consultation_access_denied(self, client, question, user_without_consultation_access, endpoint_name):
        """Test that users without consultation access cannot access any API endpoint"""
        client.force_login(user_without_consultation_access)
        url = reverse(
            endpoint_name,
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        response = client.get(url)
        assert response.status_code == 403


@pytest.mark.django_db
class TestAPIViewErrorHandling:
    """Test error handling across API views"""
    
    def test_nonexistent_consultation(self, client, consultation_user):
        """Test API endpoints with non-existent consultation"""
        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_options",
            kwargs={"consultation_slug": "nonexistent", "question_slug": "also-nonexistent"}
        )
        response = client.get(url)
        assert response.status_code == 403  # DRF returns 403 for permission denied

    def test_nonexistent_question(self, client, consultation_user, question):
        """Test API endpoints with non-existent question"""
        client.force_login(consultation_user)
        url = reverse(
            "api_demographic_options",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": "nonexistent"}
        )
        response = client.get(url)
        assert response.status_code == 404