import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
from consultation_analyser.consultations.views import filters


def set_up_for_filters():
    consultation_builder = factories.ConsultationBuilder()
    question = consultation_builder.add_question()

    theme1 = consultation_builder.add_theme(topic_keywords=["dog", "puppy"])
    theme2 = consultation_builder.add_theme(topic_keywords=["cat", "kitten"])

    for answer, theme in [
        ["We love dogs.", theme1],
        ["We like cats not dogs", theme2],
        ["We love cats", theme2],
        [None, theme2],
    ]:
        a = consultation_builder.add_answer(question, free_text=answer)
        a.themes.add(theme)

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
    queryset = filters.get_filtered_answers(question, applied_filters=applied_filters)
    assert queryset.count() == expected_count


@pytest.mark.django_db
def test_get_filtered_responses_themes():
    # Separate test, we need to get the theme ID from the generated theme
    question = set_up_for_filters()
    theme1 = models.Theme.objects.all().order_by("created_at").first()
    applied_filters = {"keyword": "", "theme": theme1.id}
    queryset = filters.get_filtered_answers(question, applied_filters=applied_filters)
    assert queryset.count() == 1
    assert queryset[0].free_text == "We love dogs."


@pytest.mark.django_db
def test_get_filtered_themes():
    question = set_up_for_filters()
    consultation = question.section.consultation
    # answers_queryset = models.Answer.objects.all()
    theme2 = models.Theme.objects.all().order_by("created_at").last()
    applied_filters = {"keyword": "", "theme": theme2.id}
    queryset = filters.get_filtered_themes(
        question=question,
        applied_filters=applied_filters,
        processing_run=consultation.latest_processing_run,
    )
    assert queryset.count() == 1
    assert queryset[0].topic_keywords == ["cat", "kitten"]
    # Delete processing runs
    models.ProcessingRun.objects.filter(consultation=consultation).delete()
    queryset = filters.get_filtered_themes(
        question=question,
        applied_filters=applied_filters,
        processing_run=consultation.latest_processing_run,
    )
    assert queryset.count() == 0
