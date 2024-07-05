import pytest

from consultation_analyser import factories
from consultation_analyser.pipeline.backends.types import TopicAssignment
from consultation_analyser.pipeline.ml_pipeline import (
    get_scatter_plot_data,
)


@pytest.mark.django_db
def test_get_scatter_plot_data():
    question = factories.QuestionFactory()
    answer1 = factories.AnswerFactory(question=question)
    answer2 = factories.AnswerFactory(question=question)

    assignments = [
        TopicAssignment(
            topic_id=1,
            topic_keywords=["one", "two"],
            answer=answer1,
            x_coordinate=2.1,
            y_coordinate=3.4,
        ),
        TopicAssignment(
            topic_id=2,
            topic_keywords=["cat", "kitten"],
            answer=answer2,
            x_coordinate=4.1,
            y_coordinate=5.0,
        ),
    ]
    scatter_data = get_scatter_plot_data(assignments)
    data = scatter_data["data"]
    expected = [
        {
            "x_coordinate": 2.1,
            "answer_id": str(answer1.id),
            "y_coordinate": 3.4,
            "answer_free_text": answer1.free_text,
            "topic_id": 1,
        },
        {
            "x_coordinate": 4.1,
            "answer_id": str(answer2.id),
            "y_coordinate": 5.0,
            "answer_free_text": answer2.free_text,
            "topic_id": 2,
        },
    ]
    assert data[0] == expected[0]
    assert data[1] == expected[1]
    assert len(data) == len(expected)


@pytest.mark.django_db
def test_get_scatter_plot_data_with_detail():
    question = factories.QuestionFactory()
    consultation = question.section.consultation
    processing_run = factories.ProcessingRunFactory(consultation=consultation)
    consultation = processing_run.consultation
    consultation_resp = factories.ConsultationResponseFactory(consultation=consultation)
    theme = factories.ThemeFactory(
        topic_id=1,
        short_description="short description",
        summary="This is a much longer descriptive summary.",
        processing_run=processing_run,
    )
    answer = factories.AnswerFactory(question=question, consultation_response=consultation_resp)
    answer.themes.add(theme)
    scatter_data = {
        "data": [
            {
                "x_coordinate": 1,
                "y_coordinate": 2,
                "answer_id": str(answer.id),
                "answer_free_text": answer.free_text,
                "topic_id": 1,
            }
        ]
    }
    topic_model_meta = theme.topic_model_metadata
    topic_model_meta.scatter_plot_data = scatter_data
    topic_model_meta.save()

    updated_data = topic_model_meta.get_scatter_plot_data_with_detail()
    assert len(updated_data) == 1
    assert "x_coordinate" in updated_data[0]
    assert "short_description" in updated_data[0]
    assert updated_data[0]["short_description"] == "short description"
