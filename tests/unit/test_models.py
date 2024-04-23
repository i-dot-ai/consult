import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models


@pytest.mark.parametrize(
    "label,expected_keywords,is_outlier", [("0_key_lock", ["key", "lock"], False), ("-1_dog_cat", ["dog", "cat"], True)]
)
@pytest.mark.django_db
def test_save_theme_to_answer(label, expected_keywords, is_outlier):
    question = factories.QuestionFactory(has_free_text=True)
    answer = factories.AnswerFactory(question=question, theme=None)
    # Check theme created and saved to answer
    answer.save_theme_to_answer(theme_label=label)
    theme = models.Theme.objects.get(keywords=expected_keywords, label=label)
    assert theme.keywords == expected_keywords
    assert theme.label == label
    assert theme.is_outlier == is_outlier
    assert answer.theme.label == label
    # Check no duplicate created
    answer.save_theme_to_answer(theme_label=label)
    themes_qs = models.Theme.objects.filter(keywords=expected_keywords, label=label)
    assert themes_qs.count() == 1


@pytest.mark.django_db
def test_multiple_choice_response_count():
    question = factories.QuestionFactory(multiple_choice_options=["Yes", "No", "Maybe"])
    answers = [
        ["Yes"],
        ["Yes"],
        ["No"],
        ["Maybe"],
        ["No"],
    ]

    for answer in answers:
        factories.AnswerFactory(question=question, multiple_choice_responses=answer)
