import numpy as np
import pandas as pd
import pytest

from consultation_analyser.consultations import ml_pipeline, models
from tests import factories


def test_get_embeddings_for_question():
    answers_list = [
        {"id": 1, "free_text": "The creaminess of the chocolate, thanks to the higher milk content."},
        {"id": 2, "free_text": "The creaminess of the chocolate, thanks to the higher milk content."},
        {"id": 3, "free_text": "The balance of sweetness, not too overpowering but just right."},
    ]
    output = ml_pipeline.get_embeddings_for_question(answers_list)
    assert len(output) == 3
    assert "embedding" in output[0].keys()
    assert np.array_equal(output[0]["embedding"], output[1]["embedding"])
    assert not np.array_equal(output[0]["embedding"], output[2]["embedding"])


@pytest.mark.django_db
def test_save_themes_to_answers():
    question = factories.QuestionFactory()
    answer1 = factories.AnswerFactory(question=question, theme=None)
    answer2 = factories.AnswerFactory(question=question, theme=None)
    answer3 = factories.AnswerFactory(question=question, theme=None)
    answers_df = pd.DataFrame(
        {
            "id": [answer1.id, answer2.id, answer3.id],
            "Topic": [-1, 0, 0],
            "Name": ["-1_x_y", "0_m_n", "0_m_n"],
            "Representation": [["x", "y"], ["m", "n"], ["m", "n"]],
        }
    )
    ml_pipeline.save_themes_to_answers(answers_df)
    themes_qs = models.Theme.objects.filter(question=question)
    assert themes_qs.count() == 2
    assert "-1_x_y" in themes_qs.values_list("label", flat=True)
    assert themes_qs.get(label="0_m_n").keywords == ["m", "n"]
