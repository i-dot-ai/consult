import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.consultations.export_user_theme import (
    get_latest_sentiment_execution_run_for_question_part,
    get_position,
)


@pytest.mark.django_db
def test_get_position():
    answer = factories.FreeTextAnswerFactory()
    execution_run1 = factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
    )
    execution_run2 = factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
    )
    factories.SentimentMappingFactory(
        answer=answer,
        sentiment_analysis_execution_run=execution_run1,
        position=models.SentimentMapping.Position.AGREEMENT,
    )
    assert get_position(answer, execution_run1) == models.SentimentMapping.Position.AGREEMENT
    assert not get_position(answer, execution_run2)


@pytest.mark.django_db
def test_get_latest_sentiment_execution_run_for_question_part():
    free_text_question_part = factories.FreeTextQuestionPartFactory(
        type=models.QuestionPart.QuestionType.FREE_TEXT
    )
    answer1 = factories.FreeTextAnswerFactory(question_part=free_text_question_part)
    answer2 = factories.FreeTextAnswerFactory(question_part=free_text_question_part)
    execution_run1 = factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
    )
    execution_run2 = factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
    )
    factories.ExecutionRunFactory(
        type=models.ExecutionRun.TaskType.SENTIMENT_ANALYSIS
    )  # Diff run not tied to this question part
    factories.SentimentMappingFactory(
        answer=answer1, sentiment_analysis_execution_run=execution_run1
    )
    factories.SentimentMappingFactory(
        answer=answer2, sentiment_analysis_execution_run=execution_run1
    )
    factories.SentimentMappingFactory(
        answer=answer2, sentiment_analysis_execution_run=execution_run2
    )
    actual = get_latest_sentiment_execution_run_for_question_part(free_text_question_part)
    assert actual == execution_run2
