import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.consultations.views.consultations import (
    get_counts_of_sentiment,
    get_top_themes_for_question,
)


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
    factories.ResponseFactory(question=question)  # No annotation/position

    actual = get_counts_of_sentiment(question)
    expected = {
        "agreement": 3,
        "disagreement": 4,
        "unclear": 2,
        "no_position": 1,
    }
    assert actual == expected


@pytest.mark.django_db
def test_get_top_themes_for_question():
    question = factories.QuestionFactory(has_free_text=True)

    # Create themes
    theme_a = factories.ThemeFactory(question=question, name="Theme A", key="A")
    theme_b = factories.ThemeFactory(question=question, name="Theme B", key="B")
    theme_c = factories.ThemeFactory(question=question, name="Theme C", key="C")

    # Create responses with annotations that include only specific themes
    for _ in range(10):
        response = factories.ResponseFactory(question=question)
        factories.ResponseAnnotationFactory(response=response, themes=[theme_a])
    for _ in range(5):
        response = factories.ResponseFactory(question=question)
        factories.ResponseAnnotationFactory(response=response, themes=[theme_b])
    for _ in range(3):
        response = factories.ResponseFactory(question=question)
        factories.ResponseAnnotationFactory(response=response, themes=[theme_c])

    actual = get_top_themes_for_question(question, number_top_themes=30)
    assert len(actual) == 3, actual
    assert actual[0]["theme"] == theme_a
    assert actual[0]["count"] == 10

    actual = get_top_themes_for_question(question, 3)
    expected = [
        {"theme": theme_a, "count": 10},
        {"theme": theme_b, "count": 5},
        {"theme": theme_c, "count": 3},
    ]
    assert actual == expected
