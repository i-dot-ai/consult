from unittest.mock import patch

import pytest
from django.conf import settings

from consultation_analyser.consultations.api.utils import (
    build_respondent_data_fast,
    build_response_filter_query,
    get_filtered_responses_with_themes,
    parse_filters_from_serializer,
)
from consultation_analyser.consultations.models import (
    MultiChoiceAnswer,
    ResponseAnnotation,
)
from consultation_analyser.factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
    ThemeFactory,
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


@pytest.mark.django_db
class TestParseFiltersFromSerializer:
    def test_empty_filters(self):
        """Test parsing empty filter data"""
        validated_data = {}
        filters = parse_filters_from_serializer(validated_data)
        assert filters == {}

    def test_all_filters(self):
        """Test parsing all types of filters"""
        validated_data = {
            "sentimentFilters": "AGREEMENT,DISAGREEMENT",
            "themeFilters": "1,2,3",
            "themesSortDirection": "ascending",
            "themesSortType": "frequency",
            "evidenceRich": True,
            "searchValue": "test search",
            "searchMode": "semantic",
            "demoFilters": ["individual:true", "region:north", "age:25-34"],
        }
        filters = parse_filters_from_serializer(validated_data)

        assert filters["sentiment_list"] == ["AGREEMENT", "DISAGREEMENT"]
        assert filters["theme_list"] == ["1", "2", "3"]
        assert filters["evidence_rich"] is True
        assert filters["search_value"] == "test search"
        assert filters["search_mode"] == "semantic"
        assert filters["demo_filters"]["individual"] == "true"
        assert filters["demo_filters"]["region"] == "north"
        assert filters["demo_filters"]["age"] == "25-34"

    def test_empty_string_filters(self):
        """Test that empty string filters are handled correctly"""
        validated_data = {"sentimentFilters": "", "themeFilters": "", "searchValue": ""}
        filters = parse_filters_from_serializer(validated_data)

        # Empty strings may still be included but with empty values
        if "sentiment_list" in filters:
            assert filters["sentiment_list"] == [""]
        if "theme_list" in filters:
            assert filters["theme_list"] == [""]
        if "search_value" in filters:
            assert filters["search_value"] == ""

    def test_demo_filters_parsing(self):
        """Test demographic filters parsing with various formats"""
        validated_data = {
            "demoFilters": [
                "simple:value",
                "with spaces:value with spaces",
                "with:colon:in:value",
                ":empty_key",
                "empty_value:",
                "no_colon",
            ]
        }
        filters = parse_filters_from_serializer(validated_data)

        demo_filters = filters["demo_filters"]
        assert demo_filters["simple"] == "value"
        assert demo_filters["with spaces"] == "value with spaces"
        assert demo_filters["with"] == "colon:in:value"  # Split on first colon only
        # Empty key/value pairs and malformed entries should be filtered out
        assert "empty_value" not in demo_filters
        assert "" not in demo_filters

    def test_demo_filters_empty_list(self):
        """Test that empty demo filters list doesn't add demo_filters key"""
        validated_data = {"demoFilters": []}
        filters = parse_filters_from_serializer(validated_data)
        assert "demo_filters" not in filters

    def test_evidence_rich_false(self):
        """Test that evidenceRich=False doesn't add evidence_rich key"""
        validated_data = {"evidenceRich": False}
        filters = parse_filters_from_serializer(validated_data)
        assert "evidence_rich" not in filters


@pytest.mark.django_db
class TestBuildResponseFilterQuery:
    def test_basic_question_filter(self, question):
        """Test that basic query always includes question filter"""
        filters = {}
        query = build_response_filter_query(filters, question)

        assert "question" in str(query)
        # Check that the query contains the question filter
        query_str = str(query)
        assert "question" in query_str

    def test_sentiment_filter(self, question):
        """Test sentiment filtering"""
        filters = {"sentiment_list": ["AGREEMENT", "DISAGREEMENT"]}
        query = build_response_filter_query(filters, question)

        assert "annotation__sentiment__in" in str(query)

    def test_evidence_rich_filter(self, question):
        """Test evidence rich filtering"""
        filters = {"evidence_rich": True}
        query = build_response_filter_query(filters, question)

        assert "annotation__evidence_rich" in str(query)

    def test_demographic_filters_boolean(self, question):
        """Test demographic filters with boolean values"""
        filters = {"demo_filters": {"individual": "true", "has_disability": "false"}}
        query = build_response_filter_query(filters, question)

        query_str = str(query)
        assert "respondent__demographics__individual" in query_str
        assert "respondent__demographics__has_disability" in query_str

    def test_demographic_filters_string(self, question):
        """Test demographic filters with string values"""
        filters = {"demo_filters": {"region": "north", "age_group": "25-34"}}
        query = build_response_filter_query(filters, question)

        query_str = str(query)
        assert "respondent__demographics__region" in query_str
        assert "respondent__demographics__age_group" in query_str

    def test_combined_filters(self, question):
        """Test multiple filters combined with AND logic"""
        filters = {
            "sentiment_list": ["AGREEMENT"],
            "evidence_rich": True,
            "demo_filters": {"individual": "true"},
        }
        query = build_response_filter_query(filters, question)

        # Should have AND logic (default for Q objects)
        query_str = str(query)
        assert "annotation__sentiment__in" in query_str
        assert "annotation__evidence_rich" in query_str
        assert "respondent__demographics__individual" in query_str


@pytest.mark.django_db
class TestGetFilteredResponsesWithThemes:
    def test_no_filters(self, question):
        """Test getting responses with no filters"""
        # Create test data
        respondent = RespondentFactory(consultation=question.consultation)
        response = ResponseFactory(question=question, respondent=respondent)

        queryset = get_filtered_responses_with_themes(question)

        assert queryset.count() == 1
        assert queryset.first() == response

    def test_demographic_filters(self, question):
        """Test filtering by demographics"""
        # Create respondents with different demographics
        respondent1 = RespondentFactory(
            consultation=question.consultation, demographics={"individual": True}
        )
        respondent2 = RespondentFactory(
            consultation=question.consultation, demographics={"individual": False}
        )

        response1 = ResponseFactory(question=question, respondent=respondent1)
        ResponseFactory(question=question, respondent=respondent2)

        # Filter for individual=true
        filters = {"demo_filters": {"individual": "true"}}
        queryset = get_filtered_responses_with_themes(question, filters)

        assert queryset.count() == 1
        assert queryset.first() == response1

    def test_theme_filters_and_logic(self, question, theme, theme2):
        """Test theme filtering uses AND logic"""
        # Create responses with different theme combinations
        respondent1 = RespondentFactory(consultation=question.consultation)
        respondent2 = RespondentFactory(consultation=question.consultation)
        respondent3 = RespondentFactory(consultation=question.consultation)

        response1 = ResponseFactory(question=question, respondent=respondent1)
        response2 = ResponseFactory(question=question, respondent=respondent2)
        response3 = ResponseFactory(question=question, respondent=respondent3)

        # Response 1: has theme1 and theme2
        annotation1 = ResponseAnnotationFactoryNoThemes(response=response1)
        annotation1.add_original_ai_themes([theme, theme2])

        # Response 2: has only theme1
        annotation2 = ResponseAnnotationFactoryNoThemes(response=response2)
        annotation2.add_original_ai_themes([theme])

        # Response 3: has only theme2
        annotation3 = ResponseAnnotationFactoryNoThemes(response=response3)
        annotation3.add_original_ai_themes([theme2])

        # Filter by theme1 AND theme2
        filters = {"theme_list": [str(theme.id), str(theme2.id)]}
        queryset = get_filtered_responses_with_themes(question, filters)

        # Should only return response1 which has both themes
        assert queryset.count() == 1
        assert queryset.first() == response1

    @patch("consultation_analyser.consultations.api.utils.embed_text")
    def test_semantic_search(self, mock_embed_text, question):
        """Test semantic search functionality"""
        # Create test responses with embeddings
        v1 = [1.0] + [0.0] * (settings.EMBEDDING_DIMENSION - 1)
        v2 = [-1.0] + [0.0] * (settings.EMBEDDING_DIMENSION - 1)

        response1 = ResponseFactory(question=question, free_text="exact match", embedding=v1)
        response2 = ResponseFactory(question=question, free_text="opposite", embedding=v2)

        # Mock the embedding function to return v1
        mock_embed_text.return_value = v1

        filters = {"search_value": "test query", "search_mode": "semantic"}
        queryset = get_filtered_responses_with_themes(question, filters)

        # Should be ordered by semantic similarity (distance)
        responses = list(queryset)
        assert responses[0] == response1  # Closest match
        assert responses[1] == response2  # Further match
        assert hasattr(responses[0], "distance")
        assert hasattr(responses[1], "distance")

    def test_keyword_search(self, question):
        """Test keyword search functionality"""
        ResponseFactory(
            question=question, free_text="Mary had a little lamb, His fleece was white as snow"
        )
        ResponseFactory(question=question, free_text="The quick brown fox jumps over the lazy dog")
        ResponseFactory(question=question, free_text="Mary loves the lamb, you know")

        filters = {"search_value": "mary lamb", "search_mode": "keyword"}
        queryset = get_filtered_responses_with_themes(question, filters)

        # Should return responses that contain the search terms
        results = list(queryset)
        assert len(results) == 2
        for response in results:
            assert "mary" in response.free_text.lower() or "lamb" in response.free_text.lower()

    def test_queryset_optimization(self, question):
        """Test that queryset uses proper optimizations"""
        respondent = RespondentFactory(consultation=question.consultation)
        ResponseFactory(question=question, respondent=respondent)

        queryset = get_filtered_responses_with_themes(question)

        # Check that prefetch_related is used
        assert hasattr(queryset, "_prefetch_related_lookups")
        assert len(queryset._prefetch_related_lookups) > 0

        # Check that select_related is used
        assert hasattr(queryset.query, "select_related")
        assert queryset.query.select_related is not False


@pytest.mark.django_db
class TestBuildRespondentDataFast:
    def test_basic_respondent_data(self, question):
        """Test building basic respondent data"""
        respondent = RespondentFactory(
            consultation=question.consultation, demographics={"individual": True, "region": "north"}
        )
        response = ResponseFactory(
            question=question,
            respondent=respondent,
            free_text="Test response",
        )
        for option in ["option1", "option2"]:
            answer = MultiChoiceAnswer.objects.create(question=response.question, text=option)
            response.chosen_options.add(answer)
        response.save()

        data = build_respondent_data_fast(response)

        assert data["identifier"] == str(respondent.identifier)
        assert data["free_text_answer_text"] == "Test response"
        assert data["demographic_data"] == {"individual": True, "region": "north"}
        assert sorted(data["multiple_choice_answer"]) == ["option1", "option2"]
        assert data["evidenceRich"] is False  # No annotation
        assert data["themes"] == []

    def test_with_annotation_evidence_rich(self, question):
        """Test respondent data with evidence rich annotation"""
        respondent = RespondentFactory(consultation=question.consultation)
        response = ResponseFactory(question=question, respondent=respondent)

        ResponseAnnotationFactory(
            response=response, evidence_rich=ResponseAnnotation.EvidenceRich.YES
        )

        data = build_respondent_data_fast(response)

        assert data["evidenceRich"] is True

    def test_with_annotation_not_evidence_rich(self, question):
        """Test respondent data with non-evidence rich annotation"""
        respondent = RespondentFactory(consultation=question.consultation)
        response = ResponseFactory(question=question, respondent=respondent)

        ResponseAnnotationFactory(
            response=response, evidence_rich=ResponseAnnotation.EvidenceRich.NO
        )

        data = build_respondent_data_fast(response)

        assert data["evidenceRich"] is False

    def test_with_themes(self, question, theme, theme2):
        """Test respondent data with themes"""
        respondent = RespondentFactory(consultation=question.consultation)
        response = ResponseFactory(question=question, respondent=respondent)

        annotation = ResponseAnnotationFactoryNoThemes(response=response)
        annotation.add_original_ai_themes([theme, theme2])

        data = build_respondent_data_fast(response)

        assert len(data["themes"]) == 2
        theme_names = {t["name"] for t in data["themes"]}
        assert theme_names == {"Theme A", "Theme B"}

        # Verify theme structure
        for theme_data in data["themes"]:
            assert "id" in theme_data
            assert "name" in theme_data
            assert "description" in theme_data

    def test_no_annotation(self, question):
        """Test respondent data when no annotation exists"""
        respondent = RespondentFactory(consultation=question.consultation)
        response = ResponseFactory(question=question, respondent=respondent)

        data = build_respondent_data_fast(response)

        assert data["evidenceRich"] is False
        assert data["themes"] == []

    def test_performance_optimized_structure(self, question):
        """Test that the function returns optimized data structure"""
        respondent = RespondentFactory(consultation=question.consultation)
        response = ResponseFactory(question=question, respondent=respondent)

        data = build_respondent_data_fast(response)

        # Verify all expected keys are present
        expected_keys = {
            "identifier",
            "free_text_answer_text",
            "demographic_data",
            "themes",
            "multiple_choice_answer",
            "evidenceRich",
        }
        assert set(data.keys()) == expected_keys
