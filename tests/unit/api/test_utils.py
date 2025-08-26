from unittest.mock import patch

import pytest
from django.conf import settings

from consultation_analyser.consultations.api.serializers import ResponseSerializer
from consultation_analyser.consultations.api.utils import (
    get_filtered_responses_with_themes,
    parse_filters_from_serializer,
)
from consultation_analyser.consultations.models import (
    MultiChoiceAnswer,
)
from consultation_analyser.factories import (
    RespondentFactory,
    ResponseAnnotationFactory,
    ResponseAnnotationFactoryNoThemes,
    ResponseFactory,
)


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
            "searchValue": "test search",
            "searchMode": "semantic",
        }
        filters = parse_filters_from_serializer(validated_data)

        assert filters["search_value"] == "test search"
        assert filters["search_mode"] == "semantic"

    def test_empty_string_filters(self):
        """Test that empty string filters are handled correctly"""
        validated_data = {"searchValue": ""}
        filters = parse_filters_from_serializer(validated_data)

        if "search_value" in filters:
            assert filters["search_value"] == ""


@pytest.mark.django_db
class TestGetFilteredResponsesWithThemes:
    def test_no_filters(self, free_text_question):
        """Test getting responses with no filters"""
        # Create test data
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response = ResponseFactory(question=free_text_question, respondent=respondent)

        queryset = get_filtered_responses_with_themes(free_text_question.response_set.all())

        assert queryset.count() == 1
        assert queryset.first() == response

    @patch("consultation_analyser.consultations.api.utils.embed_text")
    def test_semantic_search(self, mock_embed_text, free_text_question):
        """Test semantic search functionality"""
        # Create test responses with embeddings
        v1 = [1.0] + [0.0] * (settings.EMBEDDING_DIMENSION - 1)
        v2 = [-1.0] + [0.0] * (settings.EMBEDDING_DIMENSION - 1)

        response1 = ResponseFactory(
            question=free_text_question, free_text="exact match", embedding=v1
        )
        response2 = ResponseFactory(question=free_text_question, free_text="opposite", embedding=v2)

        # Mock the embedding function to return v1
        mock_embed_text.return_value = v1

        filters = {"search_value": "test query", "search_mode": "semantic"}
        queryset = get_filtered_responses_with_themes(
            free_text_question.response_set.all(), filters
        )

        # Should be ordered by semantic similarity (distance)
        responses = list(queryset)
        assert responses[0] == response1  # Closest match
        assert responses[1] == response2  # Further match
        assert hasattr(responses[0], "distance")
        assert hasattr(responses[1], "distance")

    def test_keyword_search(self, free_text_question):
        """Test keyword search functionality"""
        ResponseFactory(
            question=free_text_question,
            free_text="Mary had a little lamb, His fleece was white as snow",
        )
        ResponseFactory(
            question=free_text_question, free_text="The quick brown fox jumps over the lazy dog"
        )
        ResponseFactory(question=free_text_question, free_text="Mary loves the lamb, you know")

        filters = {"search_value": "lamb, H", "search_mode": "keyword"}
        queryset = get_filtered_responses_with_themes(
            free_text_question.response_set.all(), filters
        )

        # Should return responses that contain the search terms
        results = list(queryset)
        assert len(results) == 1
        assert "lamb, H" in results[0].free_text

    def test_queryset_optimization(self, free_text_question):
        """Test that queryset uses proper optimizations"""
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        ResponseFactory(question=free_text_question, respondent=respondent)

        queryset = get_filtered_responses_with_themes(free_text_question.response_set.all())

        # Check that prefetch_related is used
        assert hasattr(queryset, "_prefetch_related_lookups")
        assert len(queryset._prefetch_related_lookups) > 0

        # Check that select_related is used
        assert hasattr(queryset.query, "select_related")
        assert queryset.query.select_related is not False


@pytest.mark.django_db
class TestBuildRespondentDataFast:
    def test_basic_respondent_data(self, free_text_question):
        """Test building basic respondent data"""
        respondent = RespondentFactory(
            consultation=free_text_question.consultation,
            demographics={"individual": True, "region": "north"},
        )
        response = ResponseFactory(
            question=free_text_question,
            respondent=respondent,
            free_text="Test response",
        )
        for option in ["option1", "option2"]:
            answer = MultiChoiceAnswer.objects.create(question=response.question, text=option)
            response.chosen_options.add(answer)
        response.save()

        serializer = ResponseSerializer(instance=response)

        assert serializer.data["identifier"] == str(respondent.identifier)
        assert serializer.data["free_text_answer_text"] == "Test response"
        assert serializer.data["demographic_data"] == {"individual": True, "region": "north"}
        assert sorted(serializer.data["multiple_choice_answer"]) == ["option1", "option2"]
        assert serializer.data["evidenceRich"] is None  # No annotation
        assert serializer.data["themes"] is None

    def test_with_annotation_evidence_rich(self, free_text_question):
        """Test respondent data with evidence rich annotation"""
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response = ResponseFactory(question=free_text_question, respondent=respondent)

        ResponseAnnotationFactory(response=response, evidence_rich=True)

        serializer = ResponseSerializer(instance=response)

        assert serializer.data["evidenceRich"] is True

    def test_with_annotation_not_evidence_rich(self, free_text_question):
        """Test respondent data with non-evidence rich annotation"""
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response = ResponseFactory(question=free_text_question, respondent=respondent)

        ResponseAnnotationFactory(response=response, evidence_rich=False)

        serializer = ResponseSerializer(instance=response)

        assert serializer.data["evidenceRich"] is False

    def test_with_themes(self, free_text_question, theme_a, theme_b):
        """Test respondent data with themes"""
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response = ResponseFactory(question=free_text_question, respondent=respondent)

        annotation = ResponseAnnotationFactoryNoThemes(response=response)
        annotation.add_original_ai_themes([theme_a, theme_b])

        serializer = ResponseSerializer(instance=response)

        assert len(serializer.data["themes"]) == 2
        theme_names = {t["name"] for t in serializer.data["themes"]}
        assert theme_names == {"Theme A", "Theme B"}

        # Verify theme structure
        for theme_data in serializer.data["themes"]:
            assert "id" in theme_data
            assert "name" in theme_data
            assert "description" in theme_data

    def test_no_annotation(self, free_text_question):
        """Test respondent data when no annotation exists"""
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response = ResponseFactory(question=free_text_question, respondent=respondent)

        serializer = ResponseSerializer(instance=response)

        assert serializer.data["evidenceRich"] is None
        assert serializer.data["themes"] is None

    def test_performance_optimized_structure(self, free_text_question):
        """Test that the function returns optimized data structure"""
        respondent = RespondentFactory(consultation=free_text_question.consultation)
        response = ResponseFactory(question=free_text_question, respondent=respondent)

        serializer = ResponseSerializer(instance=response)

        # Verify all expected keys are present
        expected_keys = {
            "id",
            "identifier",
            "free_text_answer_text",
            "demographic_data",
            "themes",
            "multiple_choice_answer",
            "evidenceRich",
            "sentiment",
            "human_reviewed",
        }
        assert set(serializer.data.keys()) == expected_keys
