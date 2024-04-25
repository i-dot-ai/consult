import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
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
    return question


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
    question = set_up_for_filters()
    queryset = filters.get_filtered_responses(question, applied_filters=applied_filters)
    assert queryset.count() == expected_count


@pytest.mark.django_db
def test_get_filtered_responses_themes():
    # Separate test, we need to get the theme ID from the generated theme
    question = set_up_for_filters()
    theme1 = models.Theme.objects.all().order_by("created_at").first()
    applied_filters = {"keyword": "", "theme": theme1.id, "opinion": "All"}
    queryset = filters.get_filtered_responses(question, applied_filters=applied_filters)
    assert queryset.count() == 1
    assert queryset[0].free_text == "We love dogs."


@pytest.mark.django_db
def test_get_filtered_themes():
    question = set_up_for_filters()
    answers_queryset = models.Answer.objects.all()
    theme2 = models.Theme.objects.all().order_by("created_at").last()
    applied_filters = {"keyword": "", "theme": theme2.id, "opinion": "All"}
    queryset = filters.get_filtered_themes(
        question=question, filtered_answers=answers_queryset, applied_filters=applied_filters
    )
    assert queryset.count() == 1
    assert queryset[0].label == "2_cat_kitten"
