import pytest
from django.conf import settings

from consultations.api.filters import ResponseSearchFilter
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
