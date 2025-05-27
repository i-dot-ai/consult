import pytest
from django.contrib.auth.models import Group
from django.core.cache import cache

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.models import (
    ExecutionRun,
    Respondent,
    SentimentMapping,
    ThemeMapping,
)
from consultation_analyser.consultations.views.answers import (
    get_respondents_for_question,
    get_selected_option_summary,
    get_selected_theme_summary,
)
from consultation_analyser.factories import (
    EvidenceRichMappingFactory,
    ExecutionRunFactory,
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
    UserFactory,
)


@pytest.fixture()
def themefinder_respondent_id():
    return 1


@pytest.fixture()
def matching_respondent(themefinder_respondent_id):
    return RespondentFactory(themefinder_respondent_id=themefinder_respondent_id)


@pytest.fixture()
def question():
    return QuestionFactory()


@pytest.fixture()
def question_part(question):
    return FreeTextQuestionPartFactory(question=question)


@pytest.fixture()
def consultation_user(question):
    user = UserFactory()
    dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user.groups.add(dash_access)
    user.save()
    question.consultation.users.add(user)
    return user


@pytest.fixture()
def framework(question_part):
    return InitialFrameworkFactory(question_part=question_part)


@pytest.fixture()
def theme_mapping_execution_run():
    return ExecutionRunFactory(type=ExecutionRun.TaskType.THEME_MAPPING)


@pytest.fixture()
def theme_generation_execution_run():
    return ExecutionRunFactory(type=ExecutionRun.TaskType.THEME_GENERATION)


@pytest.fixture()
def evidence_evaluation_execution_run():
    return ExecutionRunFactory(type=ExecutionRun.TaskType.EVIDENCE_EVALUATION)


@pytest.fixture()
def positive_sentiment():
    return SentimentMapping.Position.AGREEMENT


@pytest.fixture()
def theme_a(framework):
    return InitialThemeFactory(framework=framework, key="A")


# TODO: delete me
@pytest.fixture()
def positive_theme_stance():
    return ThemeMapping.Stance.POSITIVE


@pytest.fixture()
def answer_matching_all_filters(
    matching_respondent,
    question_part,
    positive_sentiment,
    theme_a,
    evidence_evaluation_execution_run,
):
    answer = FreeTextAnswerFactory(respondent=matching_respondent, question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    ThemeMappingFactory(theme=theme_a, answer=answer)
    EvidenceRichMappingFactory(
        answer=answer,
        evidence_rich=True,
        evidence_evaluation_execution_run=evidence_evaluation_execution_run,
    )
    return answer


# TODO: delete me
@pytest.fixture()
def answer_not_matching_respondent_id(
    question_part, positive_sentiment, theme_a, positive_theme_stance
):
    answer = FreeTextAnswerFactory(question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    ThemeMappingFactory(theme=theme_a, stance=positive_theme_stance, answer=answer)
    return answer


@pytest.fixture()
def answer_not_matching_positive_sentiment(
    question_part, theme_a, positive_theme_stance, evidence_evaluation_execution_run
):
    answer = FreeTextAnswerFactory(question_part=question_part)
    SentimentMappingFactory(position=SentimentMapping.Position.DISAGREEMENT, answer=answer)
    ThemeMappingFactory(theme=theme_a, answer=answer)
    EvidenceRichMappingFactory(
        answer=answer,
        evidence_rich=True,
        evidence_evaluation_execution_run=evidence_evaluation_execution_run,
    )
    return answer


@pytest.fixture()
def answer_not_matching_theme(
    question_part,
    positive_sentiment,
    positive_theme_stance,
    framework,
    evidence_evaluation_execution_run,
):
    answer = FreeTextAnswerFactory(question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    theme = InitialThemeFactory(key="B", framework=framework)
    ThemeMappingFactory(theme=theme, answer=answer)
    EvidenceRichMappingFactory(
        answer=answer,
        evidence_rich=True,
        evidence_evaluation_execution_run=evidence_evaluation_execution_run,
    )
    return answer


@pytest.fixture()
def answer_not_matching_evidence_rich(
    matching_respondent,
    question_part,
    positive_sentiment,
    theme_a,
    evidence_evaluation_execution_run,
):
    answer = FreeTextAnswerFactory(respondent=matching_respondent, question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    ThemeMappingFactory(theme=theme_a, answer=answer)
    EvidenceRichMappingFactory(
        answer=answer,
        evidence_rich=False,
        evidence_evaluation_execution_run=evidence_evaluation_execution_run,
    )
    return answer


# TODO: delete me
@pytest.fixture()
def answer_not_matching_theme_stance(question_part, positive_sentiment, theme_a):
    answer = FreeTextAnswerFactory(question_part=question_part)
    SentimentMappingFactory(position=positive_sentiment, answer=answer)
    ThemeMappingFactory(theme=theme_a, stance=ThemeMapping.Stance.NEGATIVE, answer=answer)
    return answer


@pytest.mark.django_db
def test_get_selected_theme_summary(
    question_part, framework, theme_generation_execution_run, theme_mapping_execution_run
):
    theme_a = InitialThemeFactory(
        framework=framework, key="A", execution_run=theme_generation_execution_run
    )
    theme_b = InitialThemeFactory(
        framework=framework, key="B", execution_run=theme_generation_execution_run
    )
    InitialThemeFactory(framework=framework, key="C", execution_run=theme_generation_execution_run)

    answer_theme_a = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(
        theme=theme_a,
        answer=answer_theme_a,
        stance=ThemeMapping.Stance.POSITIVE,
        execution_run=theme_mapping_execution_run,
    )
    answer_theme_b = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(
        theme=theme_b,
        answer=answer_theme_b,
        stance=ThemeMapping.Stance.POSITIVE,
        execution_run=theme_mapping_execution_run,
    )
    answer_theme_a_and_b = FreeTextAnswerFactory(question_part=question_part)
    ThemeMappingFactory(
        theme=theme_a,
        answer=answer_theme_a_and_b,
        stance=ThemeMapping.Stance.POSITIVE,
        execution_run=theme_mapping_execution_run,
    )
    ThemeMappingFactory(
        theme=theme_b,
        answer=answer_theme_a_and_b,
        stance=ThemeMapping.Stance.NEGATIVE,
        execution_run=theme_mapping_execution_run,
    )

    selected_theme_mappings = get_selected_theme_summary(
        question_part,
        Respondent.objects.all(),
    )

    theme_a_summary = selected_theme_mappings.get(theme=theme_a)
    assert theme_a_summary["count"] == 2

    theme_b_summary = selected_theme_mappings.get(theme=theme_b)
    assert theme_b_summary["count"] == 2


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

    assert option_summary[0]["A"] == 2
    assert option_summary[0]["B"] == 1

    with pytest.raises(KeyError):
        option_summary[0]["C"]


@pytest.mark.django_db
def test_respondents_json(client, question, consultation_user):
    # set up responses with evidence-rich details
    question_part = FreeTextQuestionPartFactory(question=question)
    respondent_1 = RespondentFactory(
        consultation=question.consultation, themefinder_respondent_id=1
    )
    respondent_2 = RespondentFactory(
        consultation=question.consultation, themefinder_respondent_id=2
    )
    response_1 = FreeTextAnswerFactory(question_part=question_part, respondent=respondent_1)
    response_2 = FreeTextAnswerFactory(question_part=question_part, respondent=respondent_2)

    execution_run = ExecutionRunFactory()

    EvidenceRichMappingFactory(
        answer=response_1, evidence_evaluation_execution_run=execution_run, evidence_rich=True
    )
    EvidenceRichMappingFactory(
        answer=response_2, evidence_evaluation_execution_run=execution_run, evidence_rich=False
    )

    # Query json endpoint
    client.force_login(consultation_user)
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"
    )
    assert response.status_code == 200

    response_json = response.json()

    data_1 = list(filter(lambda x: x["identifier"] == 1, response_json["all_respondents"]))[0]
    assert data_1["evidenceRich"]
    data_2 = list(filter(lambda x: x["identifier"] == 2, response_json["all_respondents"]))[0]
    assert not data_2["evidenceRich"]


@pytest.mark.parametrize(
    "querystring, expected_count, has_more_pages",
    [
        ("?", 7, False),
        ("?page_size=4", 4, True),
        ("?page_size=4&page=2", 3, False),
    ],
)
@pytest.mark.django_db
def test_respondents_json_pagination(
    querystring, expected_count, has_more_pages, client, consultation_user, question_part, question
):
    for i in range(7):
        respondent = RespondentFactory(
            consultation=question.consultation, themefinder_respondent_id=i + 1
        )
        FreeTextAnswerFactory(question_part=question_part, respondent=respondent)

    client.force_login(consultation_user)
    response = client.get(
        f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/{querystring}"
    )
    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json["all_respondents"]) == expected_count
    assert response_json["has_more_pages"] == has_more_pages


@pytest.mark.django_db
def test_get_respondents_for_question():
    # Set up a couple of questions and respondents
    question_part_text = FreeTextQuestionPartFactory()
    question = question_part_text.question
    consultation = question.consultation
    question_part_option = MultipleOptionQuestionPartFactory(question=question)
    another_question = QuestionFactory(consultation=consultation)
    another_question_part = FreeTextQuestionPartFactory(question=another_question)
    respondent_a = RespondentFactory(consultation=consultation)
    respondent_b = RespondentFactory(consultation=consultation)
    respondent_c = RespondentFactory(consultation=consultation)

    # Add answers for question
    FreeTextAnswerFactory(question_part=question_part_text, respondent=respondent_a)
    FreeTextAnswerFactory(question_part=question_part_text, respondent=respondent_b)
    MultipleOptionAnswerFactory(question_part=question_part_option, respondent=respondent_a)

    # Add answers for another_question
    FreeTextAnswerFactory(question_part=another_question_part, respondent=respondent_a)
    FreeTextAnswerFactory(question_part=another_question_part, respondent=respondent_c)

    # Check we generate the right set of respondents
    cache.clear()
    respondents = get_respondents_for_question(consultation.slug, question.slug)
    assert respondents.count() == 2
    assert respondent_a in respondents
    assert respondent_c not in respondents

    # Check we correctly retrieve from cache
    cached_respondents = cache.get(f"respondents_{consultation.slug}_{question.slug}")
    assert set(cached_respondents.values_list("id", flat=True)) == set(
        respondents.values_list("id", flat=True)
    )


@pytest.mark.django_db
def test_all_respondents_json_filters(client, question, consultation_user):
    # Set up question and respondents
    question_part_text = FreeTextQuestionPartFactory(question=question)
    consultation = question.consultation
    question_part_option = MultipleOptionQuestionPartFactory(question=question)

    respondent_a = RespondentFactory(consultation=consultation)
    respondent_b = RespondentFactory(consultation=consultation)
    respondent_c = RespondentFactory(consultation=consultation)
    respondent_d = RespondentFactory(consultation=consultation)

    # Add answers for question
    answer_a = FreeTextAnswerFactory(question_part=question_part_text, respondent=respondent_a)
    answer_b = FreeTextAnswerFactory(question_part=question_part_text, respondent=respondent_b)
    answer_c = FreeTextAnswerFactory(question_part=question_part_text, respondent=respondent_c)
    MultipleOptionAnswerFactory(question_part=question_part_option, respondent=respondent_a)
    MultipleOptionAnswerFactory(question_part=question_part_option, respondent=respondent_d)

    # Add themes and sentiment/evidence to free text question part
    framework = InitialFrameworkFactory(question_part=question_part_text)
    theme_x = InitialThemeFactory(question_part=question_part_text, framework=framework, key="X")
    theme_y = InitialThemeFactory(question_part=question_part_text, framework=framework, key="Y")
    theme_z = InitialThemeFactory(question_part=question_part_text, framework=framework, key="Z")

    ThemeMappingFactory(answer=answer_a, theme=theme_x)
    ThemeMappingFactory(answer=answer_a, theme=theme_y)
    ThemeMappingFactory(answer=answer_a, theme=theme_z)
    ThemeMappingFactory(answer=answer_b, theme=theme_y)

    SentimentMappingFactory(answer=answer_a, position=SentimentMapping.Position.AGREEMENT)
    SentimentMappingFactory(answer=answer_b, position=SentimentMapping.Position.DISAGREEMENT)
    SentimentMappingFactory(answer=answer_c, position=SentimentMapping.Position.UNCLEAR)

    EvidenceRichMappingFactory(answer=answer_a, evidence_rich=True)
    EvidenceRichMappingFactory(answer=answer_b, evidence_rich=False)

    # Login user and set up endpoint
    client.force_login(consultation_user)
    base_url = f"/consultations/{question.consultation.slug}/responses/{question.slug}/json/"

    # Do we get all responses?
    response = client.get(base_url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 4
    assert {r["id"] for r in all_respondents} == {
        f"response-{respondent_a.identifier}",
        f"response-{respondent_b.identifier}",
        f"response-{respondent_c.identifier}",
        f"response-{respondent_d.identifier}",
    }
    response.json().get("has_more_pages") == False

    # Filter on sentiment
    url = f"{base_url}?sentimentFilters=AGREEMENT,DISAGREEMENT"
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 2
    assert {r["id"] for r in all_respondents} == {
        f"response-{respondent_a.identifier}",
        f"response-{respondent_b.identifier}",
    }
    response.json().get("has_more_pages") == False

    url = f"{base_url}?sentimentFilters=AGREEMENT,DISAGREEMENT,UNCLEAR"
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 3

    # Filter on theme
    url = f"{base_url}?themeFilters={theme_y.id}"
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 2

    url = f"{base_url}?themeFilters={theme_y.id},{theme_z.id}"
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 2

    # Filter on some sentiment, some theme
    url = f"{base_url}?themeFilters={theme_x.id},{theme_y.id}&sentimentFilters=UNCLEAR"
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 0

    url = (
        f"{base_url}?themeFilters={theme_x.id},{theme_y.id}&sentimentFilters=AGREEMENT,DISAGREEMENT"
    )
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 2

    # Evidence rich filter
    url = f"{base_url}?evidenceRichFilter=evidence-rich"
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 1
    assert all_respondents[0]["id"] == f"response-{respondent_a.themefinder_respondent_id}"

    url = f"{base_url}?evidenceRichFilter=evidence-rich&themeFilters={theme_y.id}"
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 1
    assert all_respondents[0]["id"] == f"response-{respondent_a.themefinder_respondent_id}"

    url = f"{base_url}?evidenceRichFilter=evidence-rich&themeFilters={theme_y.id}&sentimentFilters=UNCLEAR"
    response = client.get(url)
    all_respondents = response.json().get("all_respondents")
    assert len(all_respondents) == 0

    # TODO - add page size and page number parameters
