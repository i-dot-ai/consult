import pytest

from consultation_analyser import factories
from consultation_analyser.consultations.views import filters


def set_up_for_filters():
    question = factories.QuestionFactory()
    theme1 = factories.ThemeFactory(label="1_dog_puppy")
    theme2 = factories.ThemeFactory(label="2_cat_kitten")
    factories.AnswerFactory(
        theme=theme1, question=question, free_text="We love dogs.", multiple_choice_responses=["Option 1", "Option 2"]
    )
    factories.AnswerFactory(
        theme=theme2, question=question, free_text="We like cats not dogs.", multiple_choice_responses=["Option 1"]
    )
    factories.AnswerFactory(theme=theme2, question=question, free_text="We love cats.")
    return question, theme1


@pytest.mark.parametrize(
    "applied_filters,expected_count",
    [
        ({"theme": "All", "keyword": "", "opinion": "All"}, 3),
        ({"keyword": "dogs", "theme": "All", "opinion": "All"}, 2),
        ({"keyword": "dogs", "theme": "All", "opinion": "Option 2"}, 1),
        ({"keyword": "", "theme": "All", "opinion": "Option 1"}, 2),
    ],
)
@pytest.mark.django_db
def test_get_filtered_responses(applied_filters, expected_count):
    question, _ = set_up_for_filters()
    queryset = filters.get_filtered_responses(question, applied_filters=applied_filters)
    assert queryset.count() == expected_count


@pytest.mark.django_db
def test_get_filtered_responses_themes():
    question, theme1 = set_up_for_filters()
    applied_filters = {"keyword": "", "theme": theme1.id, "opinion": "All"}
    queryset = filters.get_filtered_responses(question, applied_filters=applied_filters)
    assert queryset.count() == 1
