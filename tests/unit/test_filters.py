import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.consultations.views import filters


def set_up_for_filters():
    consultation = factories.ConsultationFactory()
    consultation_response = factories.ConsultationResponseFactory(consultation=consultation)
    section = factories.SectionFactory(consultation=consultation)
    question = factories.QuestionFactory(
        section=section,
    )

    theme1 = factories.ThemeFactory(topic_keywords=["dog", "puppy"], question=question)
    theme2 = factories.ThemeFactory(topic_keywords=["cat", "kitten"], question=question)
    factories.AnswerFactory(
        theme=theme1,
        question=question,
        free_text="We love dogs.",
        consultation_response=consultation_response,
    )
    factories.AnswerFactory(
        theme=theme2,
        question=question,
        free_text="We like cats not dogs.",
        consultation_response=consultation_response,
    )
    factories.AnswerFactory(
        theme=theme2,
        question=question,
        free_text="We love cats.",
        consultation_response=consultation_response,
    )
    factories.AnswerFactory(
        theme=theme2,
        question=question,
        free_text=None,
        consultation_response=consultation_response,
    )
    return question


@pytest.mark.parametrize(
    "applied_filters,expected_count",
    [
        ({"keyword": "cats", "theme": "All"}, 2),
        ({"keyword": "dogs", "theme": "All"}, 2),
        ({"keyword": "", "theme": "All"}, 4),
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
    applied_filters = {"keyword": "", "theme": theme1.id}
    queryset = filters.get_filtered_responses(question, applied_filters=applied_filters)
    assert queryset.count() == 1
    assert queryset[0].free_text == "We love dogs."


@pytest.mark.django_db
def test_get_filtered_themes():
    question = set_up_for_filters()
    answers_queryset = models.Answer.objects.all()
    theme2 = models.Theme.objects.all().order_by("created_at").last()
    applied_filters = {"keyword": "", "theme": theme2.id}
    queryset = filters.get_filtered_themes(
        question=question, filtered_answers=answers_queryset, applied_filters=applied_filters
    )
    assert queryset.count() == 1
    assert queryset[0].topic_keywords == ["cat", "kitten"]
