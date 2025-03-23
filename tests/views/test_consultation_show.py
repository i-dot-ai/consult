import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import SentimentMapping, ExecutionRun
from consultation_analyser.consultations.views.consultations import (
    get_counts_of_sentiment,
    get_top_themes_for_free_text_question_part,
)


@pytest.mark.django_db
def test_get_counts_of_sentiment():
    question_part = factories.FreeTextQuestionPartFactory()
    for _ in range(3):
        answer = factories.FreeTextAnswerFactory(question_part=question_part)
        factories.SentimentMappingFactory(
            answer=answer, position=SentimentMapping.Position.AGREEMENT
        )
    for _ in range(4):
        answer = factories.FreeTextAnswerFactory(question_part=question_part)
        factories.SentimentMappingFactory(
            answer=answer, position=SentimentMapping.Position.DISAGREEMENT
        )
    for _ in range(2):
        answer = factories.FreeTextAnswerFactory(question_part=question_part)
        factories.SentimentMappingFactory(answer=answer, position=SentimentMapping.Position.UNCLEAR)
    factories.FreeTextAnswerFactory(question_part=question_part)  # No position
    actual = get_counts_of_sentiment(question_part)
    expected = {
        "agreement": 3,
        "disagreement": 4,
        "unclear": 2,
        "no_position": 1,
    }
    assert actual == expected


@pytest.mark.django_db
def test_get_top_themes_for_free_text_question_part():
    question_part = factories.FreeTextQuestionPartFactory()
    framework = factories.InitialFrameworkFactory(question_part=question_part)
    execution_run = factories.ExecutionRunFactory(type=ExecutionRun.TaskType.THEME_MAPPING)
    theme_a = factories.InitialThemeFactory(
        name="Theme A", framework=framework, execution_run=execution_run, key="A"
    )
    theme_b = factories.InitialThemeFactory(
        name="Theme B", framework=framework, execution_run=execution_run, key="B"
    )
    theme_c = factories.InitialThemeFactory(
        name="Theme C", framework=framework, execution_run=execution_run, key="C"
    )

    for _ in range(10):
        answer = factories.FreeTextAnswerFactory(question_part=question_part)
        factories.ThemeMappingFactory(answer=answer, theme=theme_a, execution_run=execution_run)
    for _ in range(5):
        answer = factories.FreeTextAnswerFactory(question_part=question_part)
        factories.ThemeMappingFactory(answer=answer, theme=theme_b, execution_run=execution_run)
    for _ in range(3):
        answer = factories.FreeTextAnswerFactory(question_part=question_part)
        factories.ThemeMappingFactory(answer=answer, theme=theme_c, execution_run=execution_run)

    actual = get_top_themes_for_free_text_question_part(question_part, number_top_themes=30)
    assert len(actual) == 3, actual
    assert actual[0]["theme"] == theme_a
    assert actual[0]["count"] == 10

    actual = get_top_themes_for_free_text_question_part(question_part, 3)
    expected = [
        {"theme": theme_a, "count": 10},
        {"theme": theme_b, "count": 5},
        {"theme": theme_c, "count": 3},
    ]
    assert actual == expected
