import math
from unittest.mock import patch

import pytest
from django.conf import settings

from consultation_analyser.consultations.api.filters import ResponseSearchFilter
from consultation_analyser.consultations.models import Response


def pad_vector(vector):
    """helper method to pad a small vector with zeros to match the database"""
    v = [0 for _ in range(settings.EMBEDDING_DIMENSION)]
    for i, value in enumerate(vector):
        v[i] = value
    return v


@pytest.mark.django_db
@patch(
    "consultation_analyser.consultations.api.filters.embed_text", return_value=pad_vector([1, 0])
)
@pytest.mark.parametrize("delta, expected", [(+0.0001, True), (-0.0001, False)])
def test_semantic_threshold_for_response_search_filter(
    mock_embed_text, respondent_1, respondent_2, free_text_question, delta, expected
):
    """we are checking just above and below the semantic-threshold boundary to see that
    ResponseSearchFilter is correctly filtering the right responses"""

    angle = 0.3 + delta

    # here we construct the vector need to match the semantic-threshold given
    # that embed_text is mocked to always return the unit vector
    embedding = pad_vector([angle, math.sqrt(1 - math.pow(angle, 2))])

    Response.objects.create(
        respondent=respondent_1,
        question=free_text_question,
        embedding=embedding,
    )

    response_search_filter = ResponseSearchFilter()

    class FakeRequest:
        def __init__(self):
            self.query_params = {"searchMode": "representative", "searchValue": "something"}

    queryset = response_search_filter.filter_queryset(FakeRequest(), Response.objects.all(), None)
    assert queryset.exists() is expected
