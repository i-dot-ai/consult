import pytest
from django.conf import settings

from consultations.api.filters import ResponseSearchFilter, get_filtered_responses
from consultations.models import Response


def pad_vector(vector):
    """helper method to pad a small vector with zeros to match the database"""
    v = [0 for _ in range(settings.EMBEDDING_DIMENSION)]
    for i, value in enumerate(vector):
        v[i] = value
    return v


@pytest.mark.django_db
def test_keyword_search_filter(respondent_1, free_text_question):
    """Test that ResponseSearchFilter correctly filters responses using keyword search"""

    response_with_match = Response.objects.create(
        respondent=respondent_1,
        question=free_text_question,
        free_text="This is about climate policy",
    )

    response_without_match = Response.objects.create(
        respondent=respondent_1,
        question=free_text_question,
        free_text="This is about other topics",
    )

    response_search_filter = ResponseSearchFilter()

    class FakeRequest:
        def __init__(self, search_value):
            self.query_params = {"searchMode": "keyword", "searchValue": search_value}

    # Test matching keyword
    queryset = response_search_filter.filter_queryset(
        FakeRequest("climate"), Response.objects.all(), None
    )
    assert queryset.count() == 1
    assert response_with_match in queryset
    assert response_without_match not in queryset

    # Test case-insensitive matching
    queryset = response_search_filter.filter_queryset(
        FakeRequest("CLIMATE"), Response.objects.all(), None
    )
    assert queryset.count() == 1

    # Test non-matching keyword
    queryset = response_search_filter.filter_queryset(
        FakeRequest("nonexistent"), Response.objects.all(), None
    )
    assert queryset.count() == 0


@pytest.mark.django_db
def test_get_filtered_responses_with_search(respondent_1, free_text_question):
    """Test that get_filtered_responses applies keyword search alongside other filters."""
    consultation_id = free_text_question.consultation.id

    Response.objects.create(
        respondent=respondent_1,
        question=free_text_question,
        free_text="This is about climate policy",
    )
    Response.objects.create(
        respondent=respondent_1,
        question=free_text_question,
        free_text="This is about housing policy",
    )
    Response.objects.create(
        respondent=respondent_1,
        question=free_text_question,
        free_text="This is about other topics",
    )

    # No filters — returns all
    results = get_filtered_responses({}, consultation_id, question_id=free_text_question.id)
    assert results.count() == 3

    # Search only — filters by keyword
    results = get_filtered_responses(
        {"searchValue": "policy", "searchMode": "keyword"},
        consultation_id,
        question_id=free_text_question.id,
    )
    assert results.count() == 2

    # More specific search
    results = get_filtered_responses(
        {"searchValue": "climate", "searchMode": "keyword"},
        consultation_id,
        question_id=free_text_question.id,
    )
    assert results.count() == 1

    # No match
    results = get_filtered_responses(
        {"searchValue": "nonexistent", "searchMode": "keyword"},
        consultation_id,
        question_id=free_text_question.id,
    )
    assert results.count() == 0


@pytest.mark.django_db
def test_get_filtered_responses_search_with_demographic_filter(
    free_text_question, northern_demographic, southern_demographic
):
    """Test that search and demographic filters combine correctly."""
    from factories import RespondentFactory

    consultation_id = free_text_question.consultation.id

    respondent_north = RespondentFactory(consultation=free_text_question.consultation)
    respondent_north.demographics.add(northern_demographic)
    Response.objects.create(
        respondent=respondent_north,
        question=free_text_question,
        free_text="Climate policy in the north",
    )

    respondent_south = RespondentFactory(consultation=free_text_question.consultation)
    respondent_south.demographics.add(southern_demographic)
    Response.objects.create(
        respondent=respondent_south,
        question=free_text_question,
        free_text="Climate policy in the south",
    )

    respondent_north_2 = RespondentFactory(consultation=free_text_question.consultation)
    respondent_north_2.demographics.add(northern_demographic)
    Response.objects.create(
        respondent=respondent_north_2,
        question=free_text_question,
        free_text="Housing policy in the north",
    )

    # Search only — 2 results with "climate"
    results = get_filtered_responses(
        {"searchValue": "climate", "searchMode": "keyword"},
        consultation_id,
        question_id=free_text_question.id,
    )
    assert results.count() == 2

    # Search + demographic filter — only northern climate response
    results = get_filtered_responses(
        {
            "searchValue": "climate",
            "searchMode": "keyword",
            "demographics": str(northern_demographic.id),
        },
        consultation_id,
        question_id=free_text_question.id,
    )
    assert results.count() == 1
