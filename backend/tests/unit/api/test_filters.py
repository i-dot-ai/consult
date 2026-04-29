from unittest.mock import patch

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
@patch("consultations.api.filters.embed_text", return_value=pad_vector([1, 0]))
def test_semantic_search_filter(mock_embed_text, respondent_1, free_text_question):
    """Test that ResponseSearchFilter orders responses by semantic distance"""

    # Create responses with different embeddings
    response_close = Response.objects.create(
        respondent=respondent_1,
        question=free_text_question,
        embedding=pad_vector([0.9, 0.436]),  # Close to [1, 0]
    )

    response_far = Response.objects.create(
        respondent=respondent_1,
        question=free_text_question,
        embedding=pad_vector([0.3, 0.954]),  # Far from [1, 0]
    )

    response_search_filter = ResponseSearchFilter()

    class FakeRequest:
        def __init__(self):
            self.query_params = {"searchMode": "semantic", "searchValue": "something"}

    queryset = response_search_filter.filter_queryset(FakeRequest(), Response.objects.all(), None)

    # Semantic search returns all responses ordered by distance
    results = list(queryset)
    assert len(results) == 2

    # The closest response should come first
    assert results[0] == response_close
    assert results[1] == response_far
