import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.parametrize(
    "input_keywords,topic_id,is_outlier",
    [(["key", "lock"], 2, False), (["dog", "cat"], -1, True)],
)
@pytest.mark.django_db
def test_save_theme_to_answer(input_keywords, topic_id, is_outlier):
    consultation = factories.ConsultationFactory()
    consultation_response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(has_free_text=True, section=section)
    answer = factories.AnswerFactory(question=question, consultation_response=consultation_response)
    processing_run = factories.ProcessingRunFactory(consultation=consultation)
    topic_model_meta = factories.TopicModelMetadataFactory()
    #  Check theme created and saved to answer
    answer.save_theme_to_answer(
        topic_keywords=input_keywords,
        topic_id=topic_id,
        processing_run=processing_run,
        topic_model_metadata=topic_model_meta,
    )
    theme = models.Theme.objects.get(topic_keywords=input_keywords)
    assert theme.topic_keywords == input_keywords
    assert theme.is_outlier == is_outlier
    latest_themes_for_answer = processing_run.get_themes_for_answer(answer_id=answer.id)
    # At the moment, we only have at most one theme for answer and processing run
    assert latest_themes_for_answer.last().topic_keywords == input_keywords
    # Check no duplicate created
    answer.save_theme_to_answer(
        topic_keywords=input_keywords,
        topic_id=topic_id,
        processing_run=processing_run,
        topic_model_metadata=topic_model_meta,
    )
    themes_qs = models.Theme.objects.filter(topic_keywords=input_keywords)
    assert themes_qs.count() == 1


@pytest.mark.django_db
def test_uniqueness_consultation_slugs():
    factories.ConsultationFactory(name="My new consultation", slug="my-new-consultation")
    with pytest.raises(IntegrityError):
        factories.ConsultationFactory(name="My new consultation 2", slug="my-new-consultation")


@pytest.mark.django_db
def test_multiple_choice_validation():
    question = factories.QuestionFactory()
    resp = factories.ConsultationResponseFactory(consultation=question.section.consultation)
    a = factories.AnswerFactory(question=question, consultation_response=resp)

    a.multiple_choice = {"totally": "invalid"}

    with pytest.raises(ValidationError):
        a.full_clean()


@pytest.mark.django_db
def test_find_answer_multiple_choice_response():
    q = factories.QuestionFactory(
        multiple_choice_questions=[("Do you agree?", ["Yes", "No", "Maybe"])]
    )
    resp = factories.ConsultationResponseFactory(consultation=q.section.consultation)

    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["Yes"])]
    )
    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["No"])]
    )
    factories.AnswerFactory(
        question=q, consultation_response=resp, multiple_choice_answers=[("Do you agree?", ["No"])]
    )

    result = models.Answer.objects.filter_multiple_choice(question="Not a question", answer="Yes")

    assert not result

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="wrong")

    assert not result

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="Yes")

    assert result.count() == 1

    result = models.Answer.objects.filter_multiple_choice(question="Do you agree?", answer="No")

    assert result.count() == 2


def set_up_consultation():
    consultation = factories.ConsultationFactory()
    consultation_response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(section=section, text="Question 1?")
    answer = factories.AnswerFactory(
        question=question, consultation_response=consultation_response, free_text="Answer 1"
    )
    for i in range(3):
        processing_run = factories.ProcessingRunFactory(consultation=consultation)
        theme = factories.ThemeFactory(
            processing_run=processing_run, short_description=f"Theme {i}"
        )
        answer.themes.add(theme)
    return consultation


@pytest.mark.django_db
def test_latest_processing_run():
    consultation1 = factories.ConsultationFactory()
    assert not consultation1.latest_processing_run
    consultation2 = set_up_consultation()
    answer = models.Answer.objects.get(free_text="Answer 1")
    question = models.Question.objects.get(text="Question 1?")
    latest_run = consultation2.latest_processing_run
    assert latest_run
    themes = latest_run.get_themes_for_answer(answer.id)
    assert themes.last().short_description == "Theme 2"
    assert "Theme 0" not in themes.values_list("short_description", flat=True)
    themes = latest_run.get_themes_for_question(question.id)
    assert themes.count() == 1  # Ensure distinct
    assert themes.last().short_description == "Theme 2"


def set_up_scatter_data() -> models.TopicModelMetadata:
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
