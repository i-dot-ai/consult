import numpy as np
import pandas as pd
import pytest
from django.conf import settings

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.pipeline import ml_pipeline


def test_get_embeddings_for_question():
    answers_list = [
        {
            "id": 1,
            "free_text": "The creaminess of the chocolate, thanks to the higher milk content.",
        },
        {
            "id": 2,
            "free_text": "The creaminess of the chocolate, thanks to the higher milk content.",
        },
        {"id": 3, "free_text": "The balance of sweetness, not too overpowering but just right."},
    ]
    output = ml_pipeline.get_embeddings_for_question(answers_list, settings.BERTOPIC_DEFAULT_EMBEDDING_MODEL)
    assert len(output) == 3
    assert "embedding" in output[0].keys()
    assert np.array_equal(output[0]["embedding"], output[1]["embedding"])
    assert not np.array_equal(output[0]["embedding"], output[2]["embedding"])


@pytest.mark.django_db
def test_save_themes_to_answers():
    consultation = factories.ConsultationFactory()
    consultation_response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(section=section)
    answer1 = factories.AnswerFactory(
        question=question, theme=None, consultation_response=consultation_response
    )
    answer2 = factories.AnswerFactory(
        question=question, theme=None, consultation_response=consultation_response
    )
    answer3 = factories.AnswerFactory(
        question=question, theme=None, consultation_response=consultation_response
    )
    answers_df = pd.DataFrame(
        {
            "id": [answer1.id, answer2.id, answer3.id],
            "Top_n_words": ["x - y", "m - n", "m - n"],
            "Topic": [-1, 1, 1],
        }
    )
    ml_pipeline.save_themes_to_answers(answers_df)
    themes_qs = models.Theme.objects.filter(question=question)
    assert themes_qs.count() == 2
    assert ["x", "y"] in themes_qs.values_list("topic_keywords", flat=True)
