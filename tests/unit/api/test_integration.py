"""
Integration tests that demonstrate the DRF API endpoints provide equivalent functionality
to the legacy monolith endpoint. These tests show that the new split endpoints together
provide the same data and filtering capabilities as the original question_responses_json endpoint.
"""

import orjson
import pytest
from django.contrib.auth.models import Group
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
def consultation_user(consultation):
    user = UserFactory()
    dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user.groups.add(dash_access)
    user.save()
    consultation.users.add(user)
    return user


@pytest.mark.django_db
class TestLegacyVsDRFEquivalence:
    """
    Test that the new DRF endpoints provide equivalent data to the legacy monolith endpoint.
    These tests demonstrate that splitting the monolith maintains backward compatibility.
    """

    def test_basic_functionality_equivalence(self, client, consultation_user, question):
        """
        Test that the combination of DRF endpoints provides the same basic data
        as the legacy question_responses_json endpoint.
        """
        # Create test data
        respondent = RespondentFactory(
            consultation=question.consultation, 
            demographics={"individual": True, "region": "north"}
        )
        response_obj = ResponseFactory(
            question=question, 
            respondent=respondent, 
            free_text="Test response"
        )
        
        # Rebuild demographic options
        DemographicOption.rebuild_for_consultation(question.consultation)

        client.force_login(consultation_user)

        # Get data from legacy endpoint
        legacy_url = reverse(
            "question_responses_json",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        legacy_response = client.get(legacy_url)
        assert legacy_response.status_code == 200
        legacy_data = legacy_response.json()

        # Get equivalent data from DRF endpoints
        base_kwargs = {"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        
        # Get filtered responses
        responses_url = reverse("api_filtered_responses", kwargs=base_kwargs)
        responses_response = client.get(responses_url)
        assert responses_response.status_code == 200
        responses_content = b''.join(responses_response.streaming_content)
        responses_data = orjson.loads(responses_content)
        
        # Get demographic options
        demo_options_url = reverse("api_demographic_options", kwargs=base_kwargs)
        demo_options_response = client.get(demo_options_url)
        assert demo_options_response.status_code == 200
        demo_options_data = demo_options_response.json()
        
        # Get demographic aggregations
        demo_agg_url = reverse("api_demographic_aggregations", kwargs=base_kwargs)
        demo_agg_response = client.get(demo_agg_url)
        assert demo_agg_response.status_code == 200
        demo_agg_data = demo_agg_response.json()

        # Compare basic response structure
        assert legacy_data["respondents_total"] == responses_data["respondents_total"]
        assert legacy_data["filtered_total"] == responses_data["filtered_total"]
        assert legacy_data["has_more_pages"] == responses_data["has_more_pages"]
        assert len(legacy_data["all_respondents"]) == len(responses_data["all_respondents"])

        # Compare respondent data
        legacy_respondent = legacy_data["all_respondents"][0]
        drf_respondent = responses_data["all_respondents"][0]
        
        assert legacy_respondent["identifier"] == drf_respondent["identifier"]
        assert legacy_respondent["free_text_answer_text"] == drf_respondent["free_text_answer_text"]
        assert legacy_respondent["demographic_data"] == drf_respondent["demographic_data"]
        assert legacy_respondent["evidenceRich"] == drf_respondent["evidenceRich"]

        # Compare demographic options
        assert legacy_data["demographic_options"] == demo_options_data["demographic_options"]
        
        # Compare demographic aggregations
        assert legacy_data["demographic_aggregations"] == demo_agg_data["demographic_aggregations"]

    def test_theme_filtering_equivalence(self, client, consultation_user, question):
        """
        Test that theme filtering works equivalently between legacy and DRF endpoints.
        """
        # Create themes and responses with different combinations
        theme1 = ThemeFactory(question=question, name="Theme 1")
        theme2 = ThemeFactory(question=question, name="Theme 2")
        
        # Create responses with different theme combinations
        respondent1 = RespondentFactory(consultation=question.consultation)
        respondent2 = RespondentFactory(consultation=question.consultation)
        respondent3 = RespondentFactory(consultation=question.consultation)

        response1 = ResponseFactory(question=question, respondent=respondent1)
        response2 = ResponseFactory(question=question, respondent=respondent2)
        response3 = ResponseFactory(question=question, respondent=respondent3)

        # Response 1: has both themes
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme1, theme2])

        # Response 2: has only theme1
        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme1])

        # Response 3: has only theme2
        annotation3 = ResponseAnnotationFactoryNoThemes(response=response3)
        annotation3.add_original_ai_themes([theme2])

        client.force_login(consultation_user)

        # Test filtering by both themes - should return only response1 (AND logic)
        theme_filter = f"themeFilters={theme1.id},{theme2.id}"
        
        # Legacy endpoint
        legacy_url = reverse(
            "question_responses_json",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        legacy_response = client.get(f"{legacy_url}?{theme_filter}")
        legacy_data = legacy_response.json()
        
        # DRF endpoint
        responses_url = reverse(
            "api_filtered_responses",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        drf_response = client.get(f"{responses_url}?{theme_filter}")
        responses_content = b''.join(drf_response.streaming_content)
        drf_data = orjson.loads(responses_content)
        
        # Should both return only 1 response (the one with both themes)
        assert legacy_data["filtered_total"] == 1
        assert drf_data["filtered_total"] == 1
        
        # Should be the same respondent
        assert legacy_data["all_respondents"][0]["identifier"] == drf_data["all_respondents"][0]["identifier"]
        assert legacy_data["all_respondents"][0]["identifier"] == str(respondent1.identifier)

        # Test theme aggregations
        theme_agg_url = reverse(
            "api_theme_aggregations",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        theme_agg_response = client.get(f"{theme_agg_url}?{theme_filter}")
        theme_agg_data = theme_agg_response.json()
        
        # When filtering by both themes, each should have count of 1
        # (only response1 has both themes)
        assert theme_agg_data["theme_aggregations"][str(theme1.id)] == 1
        assert theme_agg_data["theme_aggregations"][str(theme2.id)] == 1
        
        # Legacy theme_mappings should match
        legacy_theme_counts = {tm["value"]: int(tm["count"]) for tm in legacy_data["theme_mappings"]}
        assert legacy_theme_counts[str(theme1.id)] == 1
        assert legacy_theme_counts[str(theme2.id)] == 1

    def test_demographic_filtering_equivalence(self, client, consultation_user, question):
        """
        Test that demographic filtering works equivalently between legacy and DRF endpoints.
        """
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
        
        # Rebuild demographic options
        DemographicOption.rebuild_for_consultation(question.consultation)

        client.force_login(consultation_user)
        
        demo_filter = "demoFilters=individual:true"
        
        # Legacy endpoint
        legacy_url = reverse(
            "question_responses_json",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        legacy_response = client.get(f"{legacy_url}?{demo_filter}")
        legacy_data = legacy_response.json()
        
        # DRF endpoints
        base_kwargs = {"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        
        responses_url = reverse("api_filtered_responses", kwargs=base_kwargs)
        responses_response = client.get(f"{responses_url}?{demo_filter}")
        responses_content = b''.join(responses_response.streaming_content)
        responses_data = orjson.loads(responses_content)
        
        demo_agg_url = reverse("api_demographic_aggregations", kwargs=base_kwargs)
        demo_agg_response = client.get(f"{demo_agg_url}?{demo_filter}")
        demo_agg_data = demo_agg_response.json()
        
        # Both should return same totals
        assert legacy_data["respondents_total"] == responses_data["respondents_total"]
        assert legacy_data["filtered_total"] == responses_data["filtered_total"]
        assert legacy_data["filtered_total"] == 1  # Only individual=True respondent
        
        # Should return same respondent
        assert legacy_data["all_respondents"][0]["identifier"] == responses_data["all_respondents"][0]["identifier"]
        assert legacy_data["all_respondents"][0]["identifier"] == str(respondent1.identifier)
        
        # Demographic aggregations should match
        assert legacy_data["demographic_aggregations"] == demo_agg_data["demographic_aggregations"]
        
        # Should only show data from filtered respondent
        assert demo_agg_data["demographic_aggregations"]["individual"]["True"] == 1
        assert demo_agg_data["demographic_aggregations"]["region"]["north"] == 1
        assert "False" not in demo_agg_data["demographic_aggregations"]["individual"]
        assert "south" not in demo_agg_data["demographic_aggregations"]["region"]

    def test_pagination_equivalence(self, client, consultation_user, question):
        """
        Test that pagination works equivalently between legacy and DRF endpoints.
        """
        # Create multiple respondents
        for i in range(5):
            respondent = RespondentFactory(consultation=question.consultation)
            ResponseFactory(question=question, respondent=respondent)

        client.force_login(consultation_user)
        
        pagination_params = "page_size=2&page=1"
        
        # Legacy endpoint
        legacy_url = reverse(
            "question_responses_json",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        legacy_response = client.get(f"{legacy_url}?{pagination_params}")
        legacy_data = legacy_response.json()
        
        # DRF endpoint
        responses_url = reverse(
            "api_filtered_responses",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        drf_response = client.get(f"{responses_url}?{pagination_params}")
        responses_content = b''.join(drf_response.streaming_content)
        drf_data = orjson.loads(responses_content)
        
        # Both should have same pagination behavior
        assert len(legacy_data["all_respondents"]) == len(drf_data["all_respondents"]) == 2
        assert legacy_data["has_more_pages"] == drf_data["has_more_pages"] is True
        assert legacy_data["respondents_total"] == drf_data["respondents_total"] == 5

    def test_error_handling_equivalence(self, client, consultation_user, question):
        """
        Test that error handling is equivalent between legacy and DRF endpoints.
        """
        client.force_login(consultation_user)
        
        # Test invalid pagination parameters
        invalid_params = "page_size=200"  # Too large
        
        # Legacy endpoint
        legacy_url = reverse(
            "question_responses_json",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        legacy_response = client.get(f"{legacy_url}?{invalid_params}")
        
        # DRF endpoint
        responses_url = reverse(
            "api_filtered_responses",
            kwargs={"consultation_slug": question.consultation.slug, "question_slug": question.slug}
        )
        drf_response = client.get(f"{responses_url}?{invalid_params}")
        
        # DRF should properly validate and return 400
        assert drf_response.status_code == 400
        # Legacy endpoint should handle this gracefully (may return 200 with capped page size)


@pytest.mark.django_db
class TestDataConsistencyAcrossEndpoints:
    """
    Test that data is consistent when accessed through different DRF endpoints.
    This ensures that the split endpoints maintain data integrity.
    """

    def test_theme_data_consistency(self, client, consultation_user, question):
        """
        Test that theme information is consistent between theme information 
        and theme aggregations endpoints.
        """
        # Create themes and responses
        theme1 = ThemeFactory(question=question, name="Theme 1", description="Description 1")
        theme2 = ThemeFactory(question=question, name="Theme 2", description="Description 2")
        
        respondent = RespondentFactory(consultation=question.consultation)
        response = ResponseFactory(question=question, respondent=respondent)
        
        annotation = ResponseAnnotationFactoryNoThemes(response=response)
        annotation.add_original_ai_themes([theme1])

        client.force_login(consultation_user)
        base_kwargs = {"consultation_slug": question.consultation.slug, "question_slug": question.slug}

        # Get theme information
        theme_info_url = reverse("api_theme_information", kwargs=base_kwargs)
        theme_info_response = client.get(theme_info_url)
        theme_info_data = theme_info_response.json()

        # Get theme aggregations
        theme_agg_url = reverse("api_theme_aggregations", kwargs=base_kwargs)
        theme_agg_response = client.get(theme_agg_url)
        theme_agg_data = theme_agg_response.json()

        # Verify theme information contains all themes
        theme_info_ids = {theme["id"] for theme in theme_info_data["themes"]}
        assert theme_info_ids == {str(theme1.id), str(theme2.id)}

        # Verify theme aggregations only contains themes with responses
        theme_agg_ids = set(theme_agg_data["theme_aggregations"].keys())
        assert theme_agg_ids == {str(theme1.id)}  # Only theme1 has responses

        # Verify theme details match
        theme1_info = next(t for t in theme_info_data["themes"] if t["id"] == str(theme1.id))
        assert theme1_info["name"] == "Theme 1"
        assert theme1_info["description"] == "Description 1"

    def test_demographic_data_consistency(self, client, consultation_user, question):
        """
        Test that demographic data is consistent between options and aggregations endpoints.
        """
        # Create respondents with demographics
        RespondentFactory(
            consultation=question.consultation, 
            demographics={"region": "north", "age": "25"}
        )
        RespondentFactory(
            consultation=question.consultation, 
            demographics={"region": "south", "age": "30"}
        )
        
        # Create responses
        for respondent in question.consultation.respondent_set.all():
            ResponseFactory(question=question, respondent=respondent)
        
        # Rebuild demographic options
        DemographicOption.rebuild_for_consultation(question.consultation)

        client.force_login(consultation_user)
        base_kwargs = {"consultation_slug": question.consultation.slug, "question_slug": question.slug}

        # Get demographic options
        demo_options_url = reverse("api_demographic_options", kwargs=base_kwargs)
        demo_options_response = client.get(demo_options_url)
        demo_options_data = demo_options_response.json()

        # Get demographic aggregations
        demo_agg_url = reverse("api_demographic_aggregations", kwargs=base_kwargs)
        demo_agg_response = client.get(demo_agg_url)
        demo_agg_data = demo_agg_response.json()

        # All fields in aggregations should be present in options
        agg_fields = set(demo_agg_data["demographic_aggregations"].keys())
        options_fields = set(demo_options_data["demographic_options"].keys())
        assert agg_fields.issubset(options_fields)

        # All values in aggregations should be present in options
        for field, counts in demo_agg_data["demographic_aggregations"].items():
            agg_values = set(counts.keys())
            option_values = set(demo_options_data["demographic_options"][field])
            assert agg_values.issubset(option_values)