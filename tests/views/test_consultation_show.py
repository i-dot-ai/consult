import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.consultations.views.consultations import get_counts_of_sentiment


@pytest.mark.django_db
def test_get_counts_of_sentiment():
    question = factories.QuestionFactory()

    # Create responses with annotations and sentiment
    for _ in range(3):
        response = factories.ResponseFactory(question=question)
        factories.ResponseAnnotationFactory(
            response=response, sentiment=models.ResponseAnnotation.Sentiment.AGREEMENT
        )
    for _ in range(4):
        response = factories.ResponseFactory(question=question)
        factories.ResponseAnnotationFactory(
            response=response, sentiment=models.ResponseAnnotation.Sentiment.DISAGREEMENT
        )
    for _ in range(2):
        response = factories.ResponseFactory(question=question)
        factories.ResponseAnnotationFactory(
            response=response, sentiment=models.ResponseAnnotation.Sentiment.UNCLEAR
        )
    # Response annotated with no sentiment
    response = factories.ResponseFactory(question=question)
    factories.ResponseAnnotationFactory(
        response=response,
        sentiment=None,
    )
    # Response not annotated
    factories.ResponseFactory(question=question)

    actual = get_counts_of_sentiment(question)
    expected = {
        "agreement": 3,
        "disagreement": 4,
        "unclear": 2,
        "no_position": 2,
    }
    assert actual == expected
