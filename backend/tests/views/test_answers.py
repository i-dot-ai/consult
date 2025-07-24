from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth.models import Group
from django.test import RequestFactory

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.models import DemographicOption
from consultation_analyser.consultations.views.answers import (
    build_respondent_data,
    build_response_filter_query,
    get_demographic_aggregations_from_responses,
    get_demographic_options,
    get_filtered_responses_with_themes,
    get_theme_summary_optimized,
    parse_filters_from_request,
)
from consultation_analyser.factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactory,
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
def test_parse_filters_from_request_empty(request_factory):
    """Test parsing filters from empty request"""
    request = request_factory.get("/")
    filters = parse_filters_from_request(request)

    assert filters == {}


@pytest.mark.django_db
def test_parse_filters_from_request_all_filters(request_factory):
    """Test parsing all types of filters from request"""
    request = request_factory.get(
        "/",
        {
            "sentimentFilters": "AGREEMENT,DISAGREEMENT",
            "themeFilters": "1,2,3",
            "evidenceRich": "true",
            "searchValue": "test search",
            "demoFilters": ["individual:true", "UK region:south", "Do+you+live+in::England"],
            "themesSortDirection": "ascending",
            "themesSortType": "frequency",
        },
    )
    filters = parse_filters_from_request(request)

    assert filters["sentiment_list"] == ["AGREEMENT", "DISAGREEMENT"]
    assert filters["theme_list"] == ["1", "2", "3"]
    assert filters["evidence_rich"]
    assert filters["search_value"] == "test search"
    assert filters["demo_filters"]["individual"] == "true"
    assert filters["demo_filters"]["UK region"] == "south"
    assert filters["demo_filters"]["Do+you+live+in"] == "England"
    assert filters["themes_sort_direction"] == "ascending"
    assert filters["themes_sort_type"] == "frequency"


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
    filters = {"demo_filters": {"individual": "true", "region": "north"}}
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
        consultation=consultation, demographics={"individual": True, "region": "north", "age": 25}
    )
    RespondentFactory(
        consultation=consultation, demographics={"individual": False, "region": "south", "age": 35}
    )
    RespondentFactory(
        consultation=consultation, demographics={"individual": True, "region": "north", "age": 45}
    )

    # Rebuild demographic options from respondent data
    DemographicOption.rebuild_for_consultation(consultation)

    options = get_demographic_options(consultation)

    assert set(options["individual"]) == {"False", "True"}
    assert set(options["region"]) == {"north", "south"}
    assert set(options["age"]) == {"25", "35", "45"}


@pytest.mark.django_db
def test_demographic_option_rebuild_for_consultation(consultation):
    """Test the DemographicOption.rebuild_for_consultation method"""
    # Create respondents with different demographic data
    RespondentFactory(consultation=consultation, demographics={"category": "A", "score": 10})
    RespondentFactory(consultation=consultation, demographics={"category": "B", "score": 20})

    # Initially no demographic options should exist
    assert DemographicOption.objects.filter(consultation=consultation).count() == 0

    # Rebuild should create the options
    count = DemographicOption.rebuild_for_consultation(consultation)
    assert count == 4  # 2 categories + 2 scores

    # Verify options were created correctly
    options = DemographicOption.objects.filter(consultation=consultation)
    field_values = {(opt.field_name, opt.field_value) for opt in options}
    expected = {("category", "A"), ("category", "B"), ("score", "10"), ("score", "20")}
    assert field_values == expected

    # Test rebuilding again should clear old options and create new ones
    RespondentFactory(
        consultation=consultation, demographics={"category": "C", "new_field": "test"}
    )

    count = DemographicOption.rebuild_for_consultation(consultation)
    assert count == 6  # 3 categories + 2 scores + 1 new_field

    # Verify the new state
    options = DemographicOption.objects.filter(consultation=consultation)
    field_values = {(opt.field_name, opt.field_value) for opt in options}
    expected = {
        ("category", "A"),
        ("category", "B"),
        ("category", "C"),
        ("score", "10"),
        ("score", "20"),
        ("new_field", "test"),
    }
    assert field_values == expected


@pytest.mark.django_db
def test_get_theme_summary_optimized_no_responses(question):
    """Test theme summary with no responses"""
    theme_summary = get_theme_summary_optimized(question)
    assert theme_summary == []


@pytest.mark.django_db
def test_get_theme_summary_optimized_with_responses(question, theme, theme2):
    """Test theme summary with responses and themes"""
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

    theme_summary = get_theme_summary_optimized(question)
    # Find our specific theme in the results
    our_theme = next((t for t in theme_summary if t["theme__id"] == theme.id), None)
    assert our_theme is not None
    assert our_theme["theme__name"] == theme.name
    assert our_theme["count"] == 2

    # Now test with filters - Theme B assigned to 1 response, Theme A assigned to 2 responses
    theme_summary = get_theme_summary_optimized(
        question=question, themes_sort_type="frequency", themes_sort_direction="ascending"
    )
    theme_summary[0]["theme__name"] = theme2.name
    theme_summary = get_theme_summary_optimized(question=question, themes_sort_type="frequency")
    theme_summary[0]["theme__name"] = theme.name
    theme_summary = get_theme_summary_optimized(
        question=question, themes_sort_type="alphabetical", themes_sort_direction="ascending"
    )
    theme_summary[1]["theme__name"] = theme2.name
    theme_summary = get_theme_summary_optimized(
        question=question, themes_sort_type="alphabetical", themes_sort_direction="descending"
    )
    theme_summary[0]["theme__name"] = theme2.name


@pytest.mark.django_db
def test_question_responses_json_basic(client, consultation_user, question):
    """Test the question_responses_json endpoint basic functionality"""
    # Create some test data
    respondent = RespondentFactory(
        consultation=question.consultation, demographics={"individual": True}
    )
    response = ResponseFactory(question=question, respondent=respondent, free_text="Test response")

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
        consultation=question.consultation, demographics={"individual": True, "region": "north"}
    )
    respondent2 = RespondentFactory(
        consultation=question.consultation, demographics={"individual": False, "region": "south"}
    )

    ResponseFactory(question=question, respondent=respondent1)
    ResponseFactory(question=question, respondent=respondent2)

    # Rebuild demographic options from respondent data
    DemographicOption.rebuild_for_consultation(question.consultation)

    # Test filtering by individual=true
    client.force_login(consultation_user)
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
        "?demoFilters=individual:true"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["respondents_total"] == 2  # Total respondents
    assert data["filtered_total"] == 1  # Filtered to individuals only
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
    assert data["has_more_pages"]
    assert data["respondents_total"] == 5


@pytest.mark.django_db
def test_question_responses_json_theme_mappings(client, consultation_user, question, theme):
    """Test that theme mappings are included in response"""
    respondent = RespondentFactory(consultation=question.consultation)
    response = ResponseFactory(question=question, respondent=respondent)

    # Create annotation with theme
    annotation = ResponseAnnotationFactoryNoThemes(response=response)
    annotation.add_original_ai_themes([theme])

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
    annotation = ResponseAnnotationFactoryNoThemes(response=response)
    annotation.add_original_ai_themes([theme])

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
        consultation=question.consultation, demographics={"individual": True}
    )
    respondent2 = RespondentFactory(
        consultation=question.consultation, demographics={"individual": False}
    )

    response1 = ResponseFactory(question=question, respondent=respondent1)
    ResponseFactory(question=question, respondent=respondent2)

    # Test with demographic filter
    filters = {"demo_filters": {"individual": "true"}}
    responses = get_filtered_responses_with_themes(question, filters)

    assert responses.count() == 1
    assert responses.first().id == response1.id
    assert responses.first().respondent.demographics["individual"]


@pytest.mark.django_db
def test_human_review(client, consultation_user, question):
    """Test that human review properly preserves AI assignments and handles theme changes"""
    # Create respondent and response
    respondent = RespondentFactory(consultation=question.consultation)
    response = ResponseFactory(question=question, respondent=respondent, free_text="Test response")

    # Create themes
    ai_theme1 = ThemeFactory(question=question, name="AI Theme 1")
    ai_theme2 = ThemeFactory(question=question, name="AI Theme 2")
    human_theme = ThemeFactory(question=question, name="Human Theme")

    # Set up initial AI annotation with themes
    annotation = ResponseAnnotationFactoryNoThemes(response=response)
    annotation.add_original_ai_themes([ai_theme1, ai_theme2])

    # Verify initial state - should have 2 AI themes
    assert annotation.themes.count() == 2
    assert set(annotation.get_original_ai_themes()) == {ai_theme1, ai_theme2}
    assert annotation.get_human_reviewed_themes().count() == 0
    assert not annotation.human_reviewed

    client.force_login(consultation_user)

    # Test Case 1: Human keeps one AI theme, removes one, adds new theme
    response_obj = client.post(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/{response.id}/",
        {
            "theme": [str(ai_theme1.id), str(human_theme.id)]
        },  # Keep ai_theme1, add human_theme, remove ai_theme2
    )

    # Should redirect to show_next
    assert response_obj.status_code == 302
    assert "show-next" in response_obj.url

    # Reload annotation to check state
    annotation.refresh_from_db()

    # Verify human review tracking
    assert annotation.human_reviewed
    assert annotation.reviewed_by == consultation_user
    assert annotation.reviewed_at is not None

    # Verify original AI assignments are preserved
    original_ai_themes = set(annotation.get_original_ai_themes())
    assert original_ai_themes == {ai_theme1, ai_theme2}  # Both original AI themes preserved

    # Verify human-reviewed themes
    human_reviewed_themes = set(annotation.get_human_reviewed_themes())
    assert human_reviewed_themes == {
        ai_theme1,
        human_theme,
    }  # Human kept ai_theme1 and added human_theme

    # Verify total themes visible (union of AI and human, no duplicates)
    all_current_themes = set(annotation.themes.all())
    assert all_current_themes == {ai_theme1, ai_theme2, human_theme}

    # Test Case 2: Human removes all themes
    response_obj = client.post(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/{response.id}/",
        {"theme": []},  # No themes selected
    )

    annotation.refresh_from_db()

    # Original AI assignments should still be preserved
    assert set(annotation.get_original_ai_themes()) == {ai_theme1, ai_theme2}

    # Human-reviewed themes should be empty
    assert annotation.get_human_reviewed_themes().count() == 0

    # All themes should still be visible (original AI assignments)
    all_current_themes = set(annotation.themes.all())
    assert all_current_themes == {ai_theme1, ai_theme2}

    # Test Case 3: Human adds only new themes, keeps none of AI themes
    response_obj = client.post(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/{response.id}/",
        {"theme": [str(human_theme.id)]},  # Only human theme
    )

    annotation.refresh_from_db()

    # Original AI assignments should still be preserved
    assert set(annotation.get_original_ai_themes()) == {ai_theme1, ai_theme2}

    # Human-reviewed themes should only be the human theme
    assert set(annotation.get_human_reviewed_themes()) == {human_theme}

    # All themes should be visible
    all_current_themes = set(annotation.themes.all())
    assert all_current_themes == {ai_theme1, ai_theme2, human_theme}


@pytest.mark.django_db
def test_theme_filtering_and_logic(question):
    """Test that theme filtering uses AND logic - responses must have ALL selected themes"""
    # Create themes
    theme1 = ThemeFactory(question=question, name="Theme 1")
    theme2 = ThemeFactory(question=question, name="Theme 2")
    theme3 = ThemeFactory(question=question, name="Theme 3")

    # Create respondents and responses with different theme combinations
    # Response 1: has theme1 and theme2
    respondent1 = RespondentFactory(consultation=question.consultation)
    response1 = ResponseFactory(question=question, respondent=respondent1, free_text="Response 1")
    annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
    annotation1.add_original_ai_themes([theme1, theme2])

    # Response 2: has only theme1
    respondent2 = RespondentFactory(consultation=question.consultation)
    response2 = ResponseFactory(question=question, respondent=respondent2, free_text="Response 2")
    annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
    annotation2.add_original_ai_themes([theme1])

    # Response 3: has theme1, theme2, and theme3
    respondent3 = RespondentFactory(consultation=question.consultation)
    response3 = ResponseFactory(question=question, respondent=respondent3, free_text="Response 3")
    annotation3 = ResponseAnnotationFactoryNoThemes(response=response3)
    annotation3.add_original_ai_themes([theme1, theme2, theme3])

    # Response 4: has only theme2
    respondent4 = RespondentFactory(consultation=question.consultation)
    response4 = ResponseFactory(question=question, respondent=respondent4, free_text="Response 4")
    annotation4 = ResponseAnnotationFactoryNoThemes(response=response4)
    annotation4.add_original_ai_themes([theme2])

    # Test 1: Filter by theme1 only (OR behavior would return all 4, AND returns 3)
    filters = {"theme_list": [str(theme1.id)]}
    responses = get_filtered_responses_with_themes(question, filters)
    response_ids = set(responses.values_list("id", flat=True))

    # Should return responses that have theme1: response1, response2, response3
    assert response_ids == {response1.id, response2.id, response3.id}

    # Test 2: Filter by theme1 AND theme2
    filters = {"theme_list": [str(theme1.id), str(theme2.id)]}
    responses = get_filtered_responses_with_themes(question, filters)
    response_ids = set(responses.values_list("id", flat=True))

    # Should return only responses that have BOTH theme1 AND theme2: response1, response3
    assert response_ids == {response1.id, response3.id}

    # Test 3: Filter by all three themes
    filters = {"theme_list": [str(theme1.id), str(theme2.id), str(theme3.id)]}
    responses = get_filtered_responses_with_themes(question, filters)
    response_ids = set(responses.values_list("id", flat=True))

    # Should return only response3 which has all three themes
    assert response_ids == {response3.id}

    # Test 4: Verify theme summary counts reflect AND filtering
    # When filtering by theme1 AND theme2, the theme summary should show counts
    # only for themes appearing in responses that have BOTH theme1 AND theme2
    filters = {"theme_list": [str(theme1.id), str(theme2.id)]}
    # TODO - get responses
    filtered_responses = get_filtered_responses_with_themes(question=question, filters=filters)
    theme_summary = get_theme_summary_optimized(
        question=question, filtered_responses=filtered_responses
    )

    # Convert to dict for easier testing
    theme_counts = {t["theme__id"]: t["count"] for t in theme_summary}

    # response1 and response3 have both theme1 and theme2
    # response1 has: theme1, theme2
    # response3 has: theme1, theme2, theme3
    # So theme1 appears in 2 responses, theme2 in 2 responses, theme3 in 1 response
    assert theme_counts[theme1.id] == 2
    assert theme_counts[theme2.id] == 2
    assert theme_counts[theme3.id] == 1


@pytest.mark.django_db
@patch("consultation_analyser.consultations.views.answers.embed_text")
def test_semantic_search(fake_embed_text, consultation, question):
    filters = {"search_value": "i am a question", "search_mode": "semantic"}

    v1 = list(0 for _ in range(settings.EMBEDDING_DIMENSION))
    v1[0] = 1

    v2 = list(0 for _ in range(settings.EMBEDDING_DIMENSION))
    v2[0] = -1

    v3 = list(0 for _ in range(settings.EMBEDDING_DIMENSION))
    v3[1] = 1

    ResponseFactory(question=question, free_text="exact match", embedding=v1)
    ResponseFactory(question=question, free_text="opposite", embedding=v2)
    ResponseFactory(question=question, free_text="orthogonal", embedding=v3)

    fake_embed_text.return_value = v1

    responses = get_filtered_responses_with_themes(question, filters)
    assert [x.free_text for x in responses] == ["exact match", "orthogonal", "opposite"]
    assert [x.distance for x in responses] == [0, 1, 2]


@pytest.mark.django_db
@pytest.mark.parametrize("search_mode", ["keyword", None])
def test_lexical_search(search_mode, consultation, question):
    filters = {"search_value": "mary lambs", "search_mode": search_mode}

    texts = [
        "Mary had a little lamb, His fleece was white as snow, And everywhere that Mary went, The lamb was sure to go",
        "He followed her to school one day, Which was against the rule, It made the children laugh and play, To see a lamb at school.",
        "And so the teacher turned him out, But still he lingered near, And waited patiently about, Till Mary did appear.",
        "What makes the lamb love Mary so? The eager children cry; Why, Mary loves the lamb, you know, The teacher did reply.",
    ]

    ResponseFactory(question=question, free_text=texts[0])
    ResponseFactory(question=question, free_text=texts[1])
    ResponseFactory(question=question, free_text=texts[2])
    ResponseFactory(question=question, free_text=texts[3])

    responses = get_filtered_responses_with_themes(question, filters)
    assert [texts.index(x.free_text) for x in responses] == [0, 3]
    assert [x.distance for x in responses] == [0.02022521, 0.014059309]


@pytest.mark.django_db
def test_question_responses_json_theme_filtering_and_logic(client, consultation_user, question):
    """Test that the JSON endpoint uses AND logic for theme filtering"""
    # Create themes
    theme1 = ThemeFactory(question=question, name="Theme 1")
    theme2 = ThemeFactory(question=question, name="Theme 2")
    theme3 = ThemeFactory(question=question, name="Theme 3")

    # Create respondents and responses with different theme combinations
    # Response 1: has theme1 and theme2
    respondent1 = RespondentFactory(consultation=question.consultation)
    response1 = ResponseFactory(question=question, respondent=respondent1, free_text="Response 1")
    annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
    annotation1.add_original_ai_themes([theme1, theme2])

    # Response 2: has only theme1
    respondent2 = RespondentFactory(consultation=question.consultation)
    response2 = ResponseFactory(question=question, respondent=respondent2, free_text="Response 2")
    annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
    annotation2.add_original_ai_themes([theme1])

    # Response 3: has theme1, theme2, and theme3
    respondent3 = RespondentFactory(consultation=question.consultation)
    response3 = ResponseFactory(question=question, respondent=respondent3, free_text="Response 3")
    annotation3 = ResponseAnnotationFactoryNoThemes(response=response3)
    annotation3.add_original_ai_themes([theme1, theme2, theme3])

    # Response 4: has only theme2
    respondent4 = RespondentFactory(consultation=question.consultation)
    response4 = ResponseFactory(question=question, respondent=respondent4, free_text="Response 4")
    annotation4 = ResponseAnnotationFactoryNoThemes(response=response4)
    annotation4.add_original_ai_themes([theme2])

    client.force_login(consultation_user)

    # Test 1: Filter by theme1 only - should return 3 responses
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
        f"?themeFilters={theme1.id}"
    )
    assert response.status_code == 200
    data = response.json()

    returned_identifiers = {r["identifier"] for r in data["all_respondents"]}
    expected_identifiers = {
        str(respondent1.identifier),
        str(respondent2.identifier),
        str(respondent3.identifier),
    }
    assert returned_identifiers == expected_identifiers
    assert data["filtered_total"] == 3

    # Test 2: Filter by theme1 AND theme2 - should return only 2 responses
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
        f"?themeFilters={theme1.id},{theme2.id}"
    )
    assert response.status_code == 200
    data = response.json()

    returned_identifiers = {r["identifier"] for r in data["all_respondents"]}
    expected_identifiers = {str(respondent1.identifier), str(respondent3.identifier)}
    assert returned_identifiers == expected_identifiers
    assert data["filtered_total"] == 2

    # Test 3: Filter by all three themes - should return only 1 response
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
        f"?themeFilters={theme1.id},{theme2.id},{theme3.id}"
    )
    assert response.status_code == 200
    data = response.json()

    returned_identifiers = {r["identifier"] for r in data["all_respondents"]}
    expected_identifiers = {str(respondent3.identifier)}
    assert returned_identifiers == expected_identifiers
    assert data["filtered_total"] == 1

    # Also verify the theme counts in the theme_mappings reflect AND filtering
    theme_mapping_counts = {tm["value"]: int(tm["count"]) for tm in data["theme_mappings"]}

    # Only response3 has all three themes, so when filtering by all three:
    # Each theme should show count of 1
    assert theme_mapping_counts[str(theme1.id)] == 1
    assert theme_mapping_counts[str(theme2.id)] == 1
    assert theme_mapping_counts[str(theme3.id)] == 1


@pytest.mark.django_db
def test_concurrent_human_review_handling(client, consultation_user, question):
    """Test that concurrent human reviewers are handled correctly when reviewing the same theme"""
    # Create another user for concurrent reviewing
    user2 = UserFactory()
    dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user2.groups.add(dash_access)
    question.consultation.users.add(user2)

    # Create respondent and response
    respondent = RespondentFactory(consultation=question.consultation)
    response = ResponseFactory(question=question, respondent=respondent, free_text="Test response")

    # Create themes
    theme1 = ThemeFactory(question=question, name="Theme 1")
    theme2 = ThemeFactory(question=question, name="Theme 2")

    # Set up initial AI annotation
    annotation = ResponseAnnotationFactoryNoThemes(response=response)
    annotation.add_original_ai_themes([theme1])

    # Verify initial state
    assert not annotation.human_reviewed

    client.force_login(consultation_user)

    # User 1 gets the response for review via show_next
    response_obj = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/show-next/"
    )

    # Should redirect to the specific response
    assert response_obj.status_code == 302
    assert str(response.id) in response_obj.url

    # Now simulate user 1 reviewing the response (adds theme2, keeps theme1)
    review_response = client.post(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/{response.id}/",
        {"theme": [str(theme1.id), str(theme2.id)]},
    )

    # Should redirect to show_next
    assert review_response.status_code == 302

    # Reload annotation to verify user 1's review
    annotation.refresh_from_db()
    assert annotation.human_reviewed
    assert annotation.reviewed_by == consultation_user

    # Create a second client for user 2
    from django.test import Client

    client2 = Client()
    client2.force_login(user2)

    # User 2 tries to get next response - should not get the already reviewed response
    response_obj2 = client2.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/show-next/"
    )

    # Should get no_responses template since the only response is already reviewed
    assert response_obj2.status_code == 200
    assert "consultations/answers/no_responses.html" in [t.name for t in response_obj2.templates]

    # Now test the edge case where user 2 somehow gets the same response URL
    # (e.g., bookmarked or concurrent access before user 1 completed review)

    # Reset the annotation to unreviewed to simulate the race condition
    annotation.human_reviewed = False
    annotation.reviewed_by = None
    annotation.reviewed_at = None
    annotation.save()

    # Both users attempt to review simultaneously
    # User 1 submits review
    review_response1 = client.post(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/{response.id}/",
        {"theme": [str(theme1.id)]},  # User 1 keeps only theme1
    )

    # User 2 submits review immediately after (simulating race condition)
    review_response2 = client2.post(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/{response.id}/",
        {"theme": [str(theme2.id)]},  # User 2 wants only theme2
    )

    # Both should succeed (return 302)
    assert review_response1.status_code == 302
    assert review_response2.status_code == 302

    # Reload annotation to check final state
    annotation.refresh_from_db()

    # Should be marked as human reviewed
    assert annotation.human_reviewed

    # The last reviewer should be recorded (user 2 in this case)
    assert annotation.reviewed_by == user2

    # The final theme assignment should be from the last reviewer
    human_reviewed_themes = set(annotation.get_human_reviewed_themes())
    assert human_reviewed_themes == {theme2}

    # Original AI themes should still be preserved
    assert set(annotation.get_original_ai_themes()) == {theme1}

    # Total themes should include both original AI and final human review
    all_current_themes = set(annotation.themes.all())
    assert all_current_themes == {theme1, theme2}  # theme1 from AI, theme2 from user2's review


@pytest.mark.django_db
def test_build_respondent_data():
    question = QuestionFactory(has_free_text=True, has_multiple_choice=False)
    respondent = RespondentFactory(consultation=question.consultation, themefinder_id=5)
    response = ResponseFactory(free_text="Response 1", respondent=respondent, chosen_options=None)
    respondent = response.respondent
    question = response.question
    theme = ThemeFactory(question=question, name="Theme A")
    ResponseAnnotationFactory(
        response=response, themes=[theme], sentiment="AGREEMENT", evidence_rich="YES"
    )

    actual = build_respondent_data(response=response)
    expected = {
        "identifier": str(respondent.identifier),
        "free_text_answer_text": "Response 1",
        "demographic_data": respondent.demographics or {},
        "themes": [
            {"id": theme.id, "name": "Theme A", "description": theme.description}
        ],
        "multiple_choice_answer": [],
        "evidenceRich": True,
    }

    assert actual == expected


@pytest.mark.django_db
def test_get_demographic_aggregations_from_responses():
    # Create test data
    consultation = ConsultationFactory()
    question = QuestionFactory(consultation=consultation)

    # Create respondents with different demographic data
    respondent1 = RespondentFactory(
        consultation=consultation,
        demographics={"gender": "male", "age_group": "25-34", "region": "north"},
    )
    respondent2 = RespondentFactory(
        consultation=consultation,
        demographics={"gender": "female", "age_group": "25-34", "region": "south"},
    )
    respondent3 = RespondentFactory(
        consultation=consultation,
        demographics={"gender": "male", "age_group": "35-44", "region": "north"},
    )
    respondent4 = RespondentFactory(
        consultation=consultation,
        demographics={"gender": "female", "age_group": "25-34", "region": "north"},
    )
    # Create one respondent with empty demographics
    respondent5 = RespondentFactory(consultation=consultation, demographics={})

    # Create responses for each respondent
    ResponseFactory(respondent=respondent1, question=question)
    ResponseFactory(respondent=respondent2, question=question)
    ResponseFactory(respondent=respondent3, question=question)
    ResponseFactory(respondent=respondent4, question=question)
    ResponseFactory(respondent=respondent5, question=question)

    # Get all responses as a queryset
    from consultation_analyser.consultations.models import Response

    filtered_responses = Response.objects.filter(question=question)

    # Test the aggregation function
    result = get_demographic_aggregations_from_responses(filtered_responses)

    # Verify the aggregations
    assert result == {
        "gender": {"male": 2, "female": 2},
        "age_group": {"25-34": 3, "35-44": 1},
        "region": {"north": 3, "south": 1},
    }


@pytest.mark.django_db
def test_get_demographic_aggregations_from_responses_with_boolean_values():
    # Test with boolean demographic values
    consultation = ConsultationFactory()
    question = QuestionFactory(consultation=consultation)

    # Create respondents with boolean demographic data
    respondent1 = RespondentFactory(
        consultation=consultation, demographics={"is_individual": True, "has_disability": False}
    )
    respondent2 = RespondentFactory(
        consultation=consultation, demographics={"is_individual": True, "has_disability": True}
    )
    respondent3 = RespondentFactory(
        consultation=consultation, demographics={"is_individual": False, "has_disability": False}
    )

    # Create responses
    ResponseFactory(respondent=respondent1, question=question)
    ResponseFactory(respondent=respondent2, question=question)
    ResponseFactory(respondent=respondent3, question=question)

    # Get responses and test aggregation
    from consultation_analyser.consultations.models import Response

    filtered_responses = Response.objects.filter(question=question)
    result = get_demographic_aggregations_from_responses(filtered_responses)

    # Verify boolean values are converted to strings
    assert result == {
        "is_individual": {"True": 2, "False": 1},
        "has_disability": {"False": 2, "True": 1},
    }


@pytest.mark.django_db
def test_get_demographic_aggregations_from_responses_empty_queryset():
    # Test with empty queryset
    question = QuestionFactory()

    from consultation_analyser.consultations.models import Response

    filtered_responses = Response.objects.filter(question=question)

    result = get_demographic_aggregations_from_responses(filtered_responses)

    # Should return empty dict for empty queryset
    assert result == {}


@pytest.mark.django_db
def test_get_demographic_aggregations_from_responses_partial_demographics():
    # Test when some respondents have partial demographic data
    consultation = ConsultationFactory()
    question = QuestionFactory(consultation=consultation)

    # Create respondents with varying demographic fields
    respondent1 = RespondentFactory(
        consultation=consultation,
        demographics={"gender": "male", "age_group": "25-34"},  # has both
    )
    respondent2 = RespondentFactory(
        consultation=consultation,
        demographics={"gender": "female"},  # only has gender
    )
    respondent3 = RespondentFactory(
        consultation=consultation,
        demographics={"age_group": "35-44"},  # only has age_group
    )

    # Create responses
    ResponseFactory(respondent=respondent1, question=question)
    ResponseFactory(respondent=respondent2, question=question)
    ResponseFactory(respondent=respondent3, question=question)

    # Get responses and test aggregation
    from consultation_analyser.consultations.models import Response

    filtered_responses = Response.objects.filter(question=question)
    result = get_demographic_aggregations_from_responses(filtered_responses)

    # Verify aggregations handle partial data correctly
    assert result == {"gender": {"male": 1, "female": 1}, "age_group": {"25-34": 1, "35-44": 1}}
