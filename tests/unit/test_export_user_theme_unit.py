import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.consultations.export_user_theme import (
    get_position,
)


@pytest.mark.django_db
def test_get_position(response_1):
    # Create a response with annotation and sentiment
    factories.ResponseAnnotationFactory(
        response=response_1, sentiment=models.ResponseAnnotation.Sentiment.AGREEMENT
    )

    assert get_position(response_1) == models.ResponseAnnotation.Sentiment.AGREEMENT

    # Test response without annotation
    response_no_annotation = factories.ResponseFactory()
    assert get_position(response_no_annotation) is None
