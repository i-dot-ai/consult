import pytest

from consultation_analyser.consultations import factories, models


@pytest.mark.django_db
def test_save_theme_to_answer():
    question = factories.QuestionFactory(has_free_text=True)
    answer = factories.AnswerFactory(question=question, theme=None)
    keywords = ["key", "lock"]
    label = "0_key_lock"
    # Check theme created and saved to answer
    answer.save_theme_to_answer(theme_label=label, theme_keywords=keywords)
    theme = models.Theme.objects.get(keywords=keywords, label=label)
    assert theme.keywords == keywords
    assert theme.label == label
    assert answer.theme.label == label
    # Check no duplicate created
    answer.save_theme_to_answer(theme_label=label, theme_keywords=keywords)
    themes_qs = models.Theme.objects.filter(keywords=keywords, label=label)
    assert themes_qs.count() == 1
