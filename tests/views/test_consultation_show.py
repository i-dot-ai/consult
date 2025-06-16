import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import ResponseAnnotation
from consultation_analyser.consultations.views.consultations import (
    get_counts_of_sentiment,
    get_top_themes_for_question,
)


@pytest.mark.django_db
def test_get_counts_of_sentiment():
    # Create consultation and question using current factories
    consultation = factories.ConsultationFactory()
    question = factories.QuestionFactory(
        consultation=consultation,
        has_free_text=True,
        has_multiple_choice=False
    )
    
    # Create responses with different sentiment annotations
    for _ in range(3):
        respondent = factories.RespondentFactory(consultation=consultation)
        response = factories.ResponseFactory(question=question, respondent=respondent)
        factories.ResponseAnnotationFactory(
            response=response, sentiment=ResponseAnnotation.Sentiment.AGREEMENT
        )
    for _ in range(4):
        respondent = factories.RespondentFactory(consultation=consultation)
        response = factories.ResponseFactory(question=question, respondent=respondent)
        factories.ResponseAnnotationFactory(
            response=response, sentiment=ResponseAnnotation.Sentiment.DISAGREEMENT
        )
    for _ in range(2):
        respondent = factories.RespondentFactory(consultation=consultation)
        response = factories.ResponseFactory(question=question, respondent=respondent)
        factories.ResponseAnnotationFactory(
            response=response, sentiment=ResponseAnnotation.Sentiment.UNCLEAR
        )
    # Create response with no sentiment annotation
    respondent = factories.RespondentFactory(consultation=consultation)
    factories.ResponseFactory(question=question, respondent=respondent)
    
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
    # Create consultation and question using current factories
    consultation = factories.ConsultationFactory()
    question = factories.QuestionFactory(
        consultation=consultation,
        has_free_text=True,
        has_multiple_choice=False
    )
    
    # Create themes for the question
    theme_a = factories.ThemeFactory(name="Theme A", question=question)
    theme_b = factories.ThemeFactory(name="Theme B", question=question)
    theme_c = factories.ThemeFactory(name="Theme C", question=question)

    # Create responses and annotations with themes
    for _ in range(10):
        respondent = factories.RespondentFactory(consultation=consultation)
        response = factories.ResponseFactory(question=question, respondent=respondent)
        annotation = factories.ResponseAnnotationFactory(response=response)
        annotation.themes.clear()
        annotation.themes.add(theme_a)
        
    for _ in range(5):
        respondent = factories.RespondentFactory(consultation=consultation)
        response = factories.ResponseFactory(question=question, respondent=respondent)
        annotation = factories.ResponseAnnotationFactory(response=response)
        annotation.themes.clear()
        annotation.themes.add(theme_b)
        
    for _ in range(3):
        respondent = factories.RespondentFactory(consultation=consultation)
        response = factories.ResponseFactory(question=question, respondent=respondent)
        annotation = factories.ResponseAnnotationFactory(response=response)
        annotation.themes.clear()
        annotation.themes.add(theme_c)

    # Test with large number to get all themes
    actual = get_top_themes_for_question(question, number_top_themes=30)
    assert len(actual) == 3, actual
    assert actual[0]["theme"] == theme_a
    assert actual[0]["count"] == 10

    # Test with limit
    actual = get_top_themes_for_question(question, 3)
    expected = [
        {"theme": theme_a, "count": 10},
        {"theme": theme_b, "count": 5},
        {"theme": theme_c, "count": 3},
    ]
    assert actual == expected
