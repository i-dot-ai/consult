import pytest
from pytest_lazy_fixtures import lf

from consultation_analyser.consultations.models import Respondent, SentimentMapping, ThemeMapping
from consultation_analyser.consultations.views.answers import (
    filter_by_demographic_data,
    filter_by_response_and_theme,
    filter_by_word_count,
    get_selected_option_summary,
    get_selected_theme_summary,
)
from consultation_analyser.factories import (
    FreeTextAnswerFactory,
    FreeTextQuestionPartFactory,
    InitialFrameworkFactory,
    InitialThemeFactory,
    MultipleOptionAnswerFactory,
    MultipleOptionQuestionPartFactory,
    QuestionFactory,
    RespondentFactory,
    SentimentMappingFactory,
    ThemeMappingFactory,
)


@pytest.fixture()
def uuid():
    return "00000000-0000-0000-0000-000000000000"


@pytest.fixture()
def question():
    return QuestionFactory()


@pytest.fixture()
def question_part(question):
    return FreeTextQuestionPartFactory(question=question)


@pytest.fixture()
def framework(question_part):
    return InitialFrameworkFactory(question_part=question_part)


@pytest.fixture()
def positive_sentiment():
    return SentimentMapping.Position.AGREEMENT


@pytest.fixture()
def theme_a(framework):
    return InitialThemeFactory(framework=framework, key="A")


@pytest.fixture()
def positive_theme_stance():
    return ThemeMapping.Stance.POSITIVE


@pytest.fixture()
def answer_matching_all_filters(
    uuid, question_part, positive_sentiment, theme_a, positive_theme_stance
):
    answer = FreeTextAnswerFactory(id=uuid, question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    ThemeMappingFactory(theme=theme_a, stance=positive_theme_stance, answer=answer)
    return answer


@pytest.fixture()
def answer_not_matching_response_uuid(
    question_part, positive_sentiment, theme_a, positive_theme_stance
):
    answer = FreeTextAnswerFactory(question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    ThemeMappingFactory(theme=theme_a, stance=positive_theme_stance, answer=answer)
    return answer


@pytest.fixture()
def answer_not_matching_positive_sentiment(question_part, theme_a, positive_theme_stance):
    answer = FreeTextAnswerFactory(question_part=question_part)
    SentimentMappingFactory(position=SentimentMapping.Position.DISAGREEMENT, answer=answer)
    ThemeMappingFactory(theme=theme_a, stance=positive_theme_stance, answer=answer)
    return answer


@pytest.fixture()
def answer_not_matching_theme(question_part, positive_sentiment, positive_theme_stance, framework):
    answer = FreeTextAnswerFactory(question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    theme = InitialThemeFactory(key="B", framework=framework)
    ThemeMappingFactory(theme=theme, stance=positive_theme_stance, answer=answer)
    return answer


@pytest.fixture()
def answer_not_matching_theme_stance(question_part, positive_sentiment, theme_a):
    answer = FreeTextAnswerFactory(question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    ThemeMappingFactory(theme=theme_a, stance=ThemeMapping.Stance.NEGATIVE, answer=answer)
    return answer


@pytest.mark.django_db
@pytest.mark.parametrize(
    "responseid, responsesentiment, theme, themestance, expected",
    [
        # No filters
        (
            None,
            None,
            None,
            None,
            [
                lf("answer_matching_all_filters"),
                lf("answer_not_matching_response_uuid"),
                lf("answer_not_matching_positive_sentiment"),
                lf("answer_not_matching_theme"),
                lf("answer_not_matching_theme_stance"),
            ],
        ),  # No filters
        # One filter
        (lf("uuid"), None, None, None, [lf("answer_matching_all_filters")]),  # Filter by responseid
        (
            None,
            lf("positive_sentiment"),
            None,
            None,
            [
                lf("answer_matching_all_filters"),
                lf("answer_not_matching_response_uuid"),
                lf("answer_not_matching_theme"),
                lf("answer_not_matching_theme_stance"),
            ],
        ),  # Filter by response sentiment
        (
            None,
            None,
            [lf("theme_a")],
            None,
            [
                lf("answer_matching_all_filters"),
                lf("answer_not_matching_response_uuid"),
                lf("answer_not_matching_positive_sentiment"),
                lf("answer_not_matching_theme_stance"),
            ],
        ),  # Filter by theme
        (
            None,
            None,
            None,
            lf("positive_theme_stance"),
            [
                lf("answer_matching_all_filters"),
                lf("answer_not_matching_response_uuid"),
                lf("answer_not_matching_positive_sentiment"),
                lf("answer_not_matching_theme"),
            ],
        ),  # Filter by theme stance
        # Combination of filters
        (
            lf("uuid"),
            lf("positive_sentiment"),
            None,
            None,
            [lf("answer_matching_all_filters")],
        ),  # Filter by responseid and response sentiment
        (
            None,
            lf("positive_sentiment"),
            [lf("theme_a")],
            None,
            [
                lf("answer_matching_all_filters"),
                lf("answer_not_matching_response_uuid"),
                lf("answer_not_matching_theme_stance"),
            ],
        ),  # Filter by responseid and theme
        (
            None,
            None,
            [lf("theme_a")],
            lf("positive_theme_stance"),
            [
                lf("answer_matching_all_filters"),
                lf("answer_not_matching_response_uuid"),
                lf("answer_not_matching_positive_sentiment"),
            ],
        ),  # Filter by theme and theme stance
    ],
)
def test_filter_by_response_and_theme(
    responseid,
    responsesentiment,
    theme,
    themestance,
    expected,
    question,
    answer_matching_all_filters,
    answer_not_matching_response_uuid,
    answer_not_matching_positive_sentiment,
    answer_not_matching_theme,
    answer_not_matching_theme_stance,
):
    assert Respondent.objects.count() == 5

    filtered_respondents = filter_by_response_and_theme(
        question,
        Respondent.objects.all(),
        responseid,
        responsesentiment,
        theme,
        themestance,
    )

    assert filtered_respondents.count() == len(expected)
    for idx, respondent in enumerate(filtered_respondents):
        assert respondent == expected[idx].respondent


@pytest.mark.django_db
def test_filter_by_multiple_themes(question, question_part, framework):
    theme_a = InitialThemeFactory(framework=framework, key="A")
    theme_b = InitialThemeFactory(framework=framework, key="B")
    theme_c = InitialThemeFactory(framework=framework, key="C")

    answer_theme_a = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(theme=theme_a, answer=answer_theme_a)

    answer_theme_b = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(theme=theme_b, answer=answer_theme_b)

    answer_theme_c = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(theme=theme_c, answer=answer_theme_c)

    answer_theme_b_and_c = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(theme=theme_b, answer=answer_theme_b_and_c)
    ThemeMappingFactory(theme=theme_c, answer=answer_theme_b_and_c)

    result = filter_by_response_and_theme(
        question,
        Respondent.objects.all(),
        None,
        None,
        [theme_a, theme_b],
        None,
    )

    assert answer_theme_a.respondent in result
    assert answer_theme_b.respondent in result
    assert answer_theme_c.respondent not in result
    assert answer_theme_b_and_c.respondent in result


@pytest.mark.django_db
def test_filter_by_word_count():
    question_1 = QuestionFactory()
    qp_1 = FreeTextQuestionPartFactory(question=question_1)
    question_2 = QuestionFactory()
    qp_2 = FreeTextQuestionPartFactory(question=question_2)

    respondent_short_answer = RespondentFactory()
    FreeTextAnswerFactory(question_part=qp_1, respondent=respondent_short_answer, text="a")

    respondent_borderline_answer = RespondentFactory()
    FreeTextAnswerFactory(
        question_part=qp_1, respondent=respondent_borderline_answer, text="a b c d e"
    )

    respondent_long_answer = RespondentFactory()
    FreeTextAnswerFactory(
        question_part=qp_1, respondent=respondent_long_answer, text="a b c d e f g h"
    )

    respondent_long_answer_other_question = RespondentFactory()
    FreeTextAnswerFactory(
        question_part=qp_1, respondent=respondent_long_answer_other_question, text="a"
    )
    FreeTextAnswerFactory(
        question_part=qp_2, respondent=respondent_long_answer_other_question, text="a b c d e f g h"
    )

    result = filter_by_word_count(Respondent.objects.all(), question_1.slug, 5)

    assert respondent_borderline_answer in result
    assert respondent_long_answer in result
    assert respondent_short_answer not in result
    assert respondent_long_answer_other_question not in result


@pytest.mark.django_db
@pytest.mark.parametrize(
    "individual_filter, should_filter",
    [
        (["individual"], True),
        (None, False),
    ],
)
def test_filter_by_demographic_data(individual_filter, should_filter):
    respondent_individual = RespondentFactory(data={"individual": "individual"})
    respondent_organisation = RespondentFactory(data={"individual": "organisation"})
    respondent_no_data = RespondentFactory()
    respondent_no_individual_data = RespondentFactory(data={"age": "18-24"})

    has_individual_data, filtered_respondents = filter_by_demographic_data(
        Respondent.objects.all(),
        individual_filter,
    )

    assert has_individual_data
    assert respondent_individual in filtered_respondents

    if should_filter:
        assert respondent_organisation not in filtered_respondents
        assert respondent_no_data not in filtered_respondents
        assert respondent_no_individual_data not in filtered_respondents
    else:
        assert respondent_organisation in filtered_respondents
        assert respondent_no_data in filtered_respondents
        assert respondent_no_individual_data in filtered_respondents


@pytest.mark.django_db
def test_get_selected_theme_summary(question_part, framework):
    theme_a = InitialThemeFactory(framework=framework, key="A")
    theme_b = InitialThemeFactory(framework=framework, key="B")
    InitialThemeFactory(framework=framework, key="C")

    answer_theme_a = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(
        theme=theme_a,
        answer=answer_theme_a,
        stance=ThemeMapping.Stance.POSITIVE,
        execution_run=framework.execution_run,
    )
    answer_theme_b = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(
        theme=theme_b,
        answer=answer_theme_b,
        stance=ThemeMapping.Stance.POSITIVE,
        execution_run=framework.execution_run,
    )
    answer_theme_a_and_b = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(
        theme=theme_a,
        answer=answer_theme_a_and_b,
        stance=ThemeMapping.Stance.POSITIVE,
        execution_run=framework.execution_run,
    )
    ThemeMappingFactory(
        theme=theme_b,
        answer=answer_theme_a_and_b,
        stance=ThemeMapping.Stance.NEGATIVE,
        execution_run=framework.execution_run,
    )

    selected_theme_mappings, theme_mapping_summary = get_selected_theme_summary(
        question_part,
        Respondent.objects.all(),
    )

    theme_a_summary = selected_theme_mappings.get(theme=theme_a)
    assert theme_a_summary["count"] == 2
    assert theme_a_summary["positive_count"] == 2
    assert theme_a_summary["negative_count"] == 0

    theme_b_summary = selected_theme_mappings.get(theme=theme_b)
    assert theme_b_summary["count"] == 2
    assert theme_b_summary["positive_count"] == 1
    assert theme_b_summary["negative_count"] == 1

    assert theme_mapping_summary["total"] == 4
    assert theme_mapping_summary["positive"] == 3
    assert theme_mapping_summary["negative"] == 1


@pytest.mark.django_db
def test_get_selected_option_summary(question):
    question_part = MultipleOptionQuestionPartFactory(question=question, options=["A", "B", "C"])

    respondent_a = RespondentFactory(consultation=question.consultation)
    respondent_b = RespondentFactory(consultation=question.consultation)
    respondent_c = RespondentFactory(consultation=question.consultation)

    MultipleOptionAnswerFactory(
        question_part=question_part, respondent=respondent_a, chosen_options=["A", "B"]
    )
    MultipleOptionAnswerFactory(
        question_part=question_part, respondent=respondent_b, chosen_options=["A"]
    )
    MultipleOptionAnswerFactory(
        question_part=question_part, respondent=respondent_c, chosen_options=[]
    )

    option_summary = get_selected_option_summary(
        question,
        Respondent.objects.all(),
    )

    print(option_summary)

    assert option_summary[0]["A"] == 2
    assert option_summary[0]["B"] == 1

    with pytest.raises(KeyError):
        option_summary[0]["C"]
