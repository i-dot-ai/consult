import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.views.answers import (
    parse_filters_from_request,
    build_response_filter_query,
    get_theme_summary_optimized,
    get_demographic_options,
    get_filtered_responses_with_themes,
)
from consultation_analyser.factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
    ResponseAnnotationFactory,
    ThemeFactory,
    UserFactory,
)


@pytest.fixture()
def consultation():
    return ConsultationFactory()


@pytest.fixture()
def question(consultation):
    return QuestionFactory(
        consultation=consultation,
        has_free_text=True,
        has_multiple_choice=False
    )


@pytest.fixture()
def theme(question):
    return ThemeFactory(question=question)


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
def test_parse_filters_from_request_empty(request_factory):
    """Test parsing filters from empty request"""
    request = request_factory.get("/")
    filters = parse_filters_from_request(request)
    
    assert filters == {}


@pytest.mark.django_db
def test_parse_filters_from_request_all_filters(request_factory):
    """Test parsing all types of filters from request"""
    request = request_factory.get(
        "/", {
            "sentimentFilters": "AGREEMENT,DISAGREEMENT",
            "themeFilters": "1,2,3",
            "evidenceRichFilter": "evidence-rich",
            "searchValue": "test search",
            "demographicFilters[individual]": "true,false",
            "demographicFilters[region]": "north,south",
        }
    )
    filters = parse_filters_from_request(request)
    
    assert filters["sentiment_list"] == ["AGREEMENT", "DISAGREEMENT"]
    assert filters["theme_list"] == ["1", "2", "3"]
    assert filters["evidence_rich"] == True
    assert filters["search_value"] == "test search"
    assert filters["demographic_filters"]["individual"] == ["true", "false"]
    assert filters["demographic_filters"]["region"] == ["north", "south"]


@pytest.mark.django_db
def test_build_response_filter_query_basic(question):
    """Test building basic filter query"""
    filters = {"sentiment_list": ["AGREEMENT"]}
    query = build_response_filter_query(filters, question)
    
    # Should include question filter and sentiment filter
    assert "question" in str(query)
    assert "annotation__sentiment__in" in str(query)


@pytest.mark.django_db
def test_build_response_filter_query_demographic_filters(question):
    """Test building filter query with demographic filters"""
    filters = {
        "demographic_filters": {
            "individual": ["true"],
            "region": ["north", "south"]
        }
    }
    query = build_response_filter_query(filters, question)
    
    # Should include demographic filters
    assert "respondent__demographics__individual" in str(query)
    assert "respondent__demographics__region" in str(query)


@pytest.mark.django_db
def test_get_demographic_options_empty(consultation):
    """Test getting demographic options with no respondents"""
    options = get_demographic_options(consultation)
    assert options == {}


@pytest.mark.django_db
def test_get_demographic_options_with_data(consultation):
    """Test getting demographic options with respondent data"""
    # Create respondents with different demographic data
    RespondentFactory(
        consultation=consultation,
        demographics={"individual": True, "region": "north", "age": 25}
    )
    RespondentFactory(
        consultation=consultation,
        demographics={"individual": False, "region": "south", "age": 35}
    )
    RespondentFactory(
        consultation=consultation,
        demographics={"individual": True, "region": "north", "age": 45}
    )
    
    options = get_demographic_options(consultation)
    
    assert set(options["individual"]) == {"False", "True"}
    assert set(options["region"]) == {"north", "south"}
    assert set(options["age"]) == {"25", "35", "45"}


@pytest.mark.django_db
def test_get_theme_summary_optimized_no_responses(question):
    """Test theme summary with no responses"""
    theme_summary = get_theme_summary_optimized(question)
    assert theme_summary == []


@pytest.mark.django_db
def test_get_theme_summary_optimized_with_responses(question, theme):
    """Test theme summary with responses and themes"""
    # Create respondents and responses
    respondent1 = RespondentFactory(consultation=question.consultation)
    respondent2 = RespondentFactory(consultation=question.consultation)
    
    response1 = ResponseFactory(question=question, respondent=respondent1)
    response2 = ResponseFactory(question=question, respondent=respondent2)
    
    # Create annotations with themes
    annotation1 = ResponseAnnotationFactory(response=response1)
    annotation1.themes.clear()  # Clear any auto-generated themes
    annotation1.themes.add(theme)
    
    annotation2 = ResponseAnnotationFactory(response=response2)
    annotation2.themes.clear()  # Clear any auto-generated themes
    annotation2.themes.add(theme)
    
    theme_summary = get_theme_summary_optimized(question)
    
    # Find our specific theme in the results
    our_theme = next((t for t in theme_summary if t["theme__id"] == theme.id), None)
    assert our_theme is not None
    assert our_theme["theme__name"] == theme.name
    assert our_theme["count"] == 2


@pytest.mark.django_db
def test_question_responses_json_basic(client, consultation_user, question):
    """Test the question_responses_json endpoint basic functionality"""
    # Create some test data
    respondent = RespondentFactory(
        consultation=question.consultation,
        demographics={"individual": True}
    )
    response = ResponseFactory(
        question=question,
        respondent=respondent,
        free_text="Test response"
    )
    
    # Make request
    client.force_login(consultation_user)
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "all_respondents" in data
    assert "respondents_total" in data
    assert "filtered_total" in data
    assert "theme_mappings" in data
    assert "demographic_options" in data
    assert data["respondents_total"] == 1
    assert data["filtered_total"] == 1


@pytest.mark.django_db
def test_question_responses_json_with_demographic_filters(client, consultation_user, question):
    """Test the question_responses_json endpoint with demographic filtering"""
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
    
    # Test filtering by individual=true
    client.force_login(consultation_user)
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
        "?demographicFilters[individual]=true"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["respondents_total"] == 2  # Total respondents
    assert data["filtered_total"] == 1     # Filtered to individuals only
    assert data["demographic_options"]["individual"] == ["False", "True"]
    assert data["demographic_options"]["region"] == ["north", "south"]


@pytest.mark.django_db
def test_question_responses_json_pagination(client, consultation_user, question):
    """Test pagination in question_responses_json"""
    # Create multiple respondents
    for i in range(5):
        respondent = RespondentFactory(consultation=question.consultation)
        ResponseFactory(question=question, respondent=respondent)
    
    client.force_login(consultation_user)
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
        "?page_size=2&page=1"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["all_respondents"]) == 2
    assert data["has_more_pages"] == True
    assert data["respondents_total"] == 5


@pytest.mark.django_db 
def test_question_responses_json_theme_mappings(client, consultation_user, question, theme):
    """Test that theme mappings are included in response"""
    respondent = RespondentFactory(consultation=question.consultation)
    response = ResponseFactory(question=question, respondent=respondent)
    
    # Create annotation with theme
    annotation = ResponseAnnotationFactory(response=response)
    annotation.themes.clear()  # Clear any auto-generated themes
    annotation.themes.add(theme)
    
    client.force_login(consultation_user)
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Find our specific theme in the mappings
    our_theme = next((t for t in data["theme_mappings"] if t["label"] == theme.name), None)
    assert our_theme is not None
    assert our_theme["count"] == "1"


@pytest.mark.django_db
def test_get_filtered_responses_with_themes_no_filters(question):
    """Test get_filtered_responses_with_themes with no filters"""
    respondent = RespondentFactory(consultation=question.consultation)
    response = ResponseFactory(question=question, respondent=respondent)
    theme = ThemeFactory(question=question)
    
    # Create annotation with theme
    annotation = ResponseAnnotationFactory(response=response)
    annotation.themes.clear()
    annotation.themes.add(theme)
    
    # Test with no filters
    responses = get_filtered_responses_with_themes(question)
    
    assert responses.count() == 1
    assert responses.first().id == response.id
    assert responses.first().annotation.themes.count() == 1


@pytest.mark.django_db
def test_get_filtered_responses_with_themes_with_filters(question):
    """Test get_filtered_responses_with_themes with filters"""
    # Create two respondents with different demographics
    respondent1 = RespondentFactory(
        consultation=question.consultation,
        demographics={"individual": True}
    )
    respondent2 = RespondentFactory(
        consultation=question.consultation,
        demographics={"individual": False}
    )
    
    response1 = ResponseFactory(question=question, respondent=respondent1)
    ResponseFactory(question=question, respondent=respondent2)
    
    # Test with demographic filter
    filters = {"demographic_filters": {"individual": ["true"]}}
    responses = get_filtered_responses_with_themes(question, filters)
    
    assert responses.count() == 1
    assert responses.first().id == response1.id
    assert responses.first().respondent.demographics["individual"]