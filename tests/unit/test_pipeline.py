import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.models import Theme, TopicModelMetadata
from consultation_analyser.consultations.views.questions import filter_scatter_plot_data
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


def set_up_scatter_data() -> TopicModelMetadata:
    question = factories.QuestionFactory()
    consultation = question.section.consultation
    processing_run = factories.ProcessingRunFactory(consultation=consultation)
    consultation = processing_run.consultation
    consultation_resp = factories.ConsultationResponseFactory(consultation=consultation)
    theme1 = factories.ThemeFactory(
        topic_id=1,
        short_description="short description",
        summary="This is a much longer descriptive summary.",
        processing_run=processing_run,
    )
    topic_model_meta = theme1.topic_model_metadata
    theme2 = factories.ThemeFactory(
        topic_id=2,
        short_description="short description 2",
        summary="descriptive summary 2",
        processing_run=processing_run,
        topic_model_metadata=topic_model_meta,
    )

    answer1 = factories.AnswerFactory(question=question, consultation_response=consultation_resp)
    answer1.themes.add(theme1)
    answer2 = factories.AnswerFactory(
        question=question, consultation_response=consultation_resp, free_text="free text 2"
    )
    answer2.themes.add(theme1)
    answer3 = factories.AnswerFactory(question=question, consultation_response=consultation_resp)
    answer3.themes.add(theme2)
    scatter_data = {
        "data": [
            {
                "x_coordinate": 1,
                "y_coordinate": 2,
                "answer_id": str(answer1.id),
                "answer_free_text": answer1.free_text,
                "topic_id": 1,
            },
            {
                "x_coordinate": 3,
                "y_coordinate": 5,
                "answer_id": str(answer2.id),
                "answer_free_text": answer2.free_text,
                "topic_id": 1,
            },
            {
                "x_coordinate": 1.3,
                "y_coordinate": 4.6,
                "answer_id": str(answer3.id),
                "answer_free_text": answer3.free_text,
                "topic_id": 2,
            },
        ]
    }
    topic_model_meta = theme1.topic_model_metadata
    topic_model_meta.scatter_plot_data = scatter_data
    topic_model_meta.save()
    return topic_model_meta


@pytest.mark.django_db
def test_add_llm_summarisation_detail():
    topic_model_meta = set_up_scatter_data()
    topic_model_meta.add_llm_summarisation_detail()
    updated_data = topic_model_meta.scatter_plot_data["data"]
    assert len(updated_data) == 3
    assert "x_coordinate" in updated_data[0]
    assert "short_description" in updated_data[0]
    assert updated_data[0]["short_description"] == "short description"
    assert updated_data[1]["short_description"] == "short description"
    assert updated_data[2]["summary"] == "descriptive summary 2"


@pytest.mark.django_db
def test_filter_scatter_plot_data():
    topic_model_meta = set_up_scatter_data()
    topic_model_meta.add_llm_summarisation_detail()

    themes_qs = Theme.objects.all()
    data = filter_scatter_plot_data(themes_qs)
    assert len(data) == 3
    assert "x_coordinate" in data[0]
    assert "short_description" in data[0]
    assert data[0]["short_description"] == "short description"
    assert data[1]["short_description"] == "short description"
    assert data[2]["summary"] == "descriptive summary 2"

    themes_qs = Theme.objects.filter(topic_id=1)
    data = filter_scatter_plot_data(themes_qs)
    assert len(data) == 2
    assert data[0]["y_coordinate"] == 2
    assert data[1]["answer_free_text"] == "free text 2"

    themes_qs = Theme.objects.none()
    data = filter_scatter_plot_data(themes_qs)
    assert data == []
