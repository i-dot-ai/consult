from types import SimpleNamespace

import pytest
import structlog
import yaml
from django.contrib.postgres.search import SearchVector
from django.test import RequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

import factories
from consultations.models import (
    Consultation,
    DemographicOption,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)
from factories import (
    CandidateThemeFactory,
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
    SelectedThemeFactory,
    UserFactory,
)


@pytest.fixture(autouse=True)
def _reset_structlog_contextvars():
    """Isolate structlog's process-global context between tests.

    settings.LOGGER and data_pipeline.batch.submit_job read/write
    structlog.contextvars, which persists across tests in a session. Without
    this, a context_id bound by one test (e.g. via refresh_context()) leaks into
    another and causes order-dependent failures under pytest --random-order.
    """
    structlog.contextvars.clear_contextvars()
    yield
    structlog.contextvars.clear_contextvars()


@pytest.fixture()
def request_factory():
    return RequestFactory()


@pytest.fixture()
def non_staff_user():
    """User with access to only their consultations"""
    user = UserFactory()
    user.save()
    yield user
    user.delete()


@pytest.fixture
def staff_user():
    """User with access to all consultations"""
    user = UserFactory(is_staff=True)
    yield user
    user.delete()


@pytest.fixture
def non_staff_user_token(non_staff_user):
    refresh = RefreshToken.for_user(non_staff_user)
    yield str(refresh.access_token)


@pytest.fixture
def staff_user_token(staff_user):
    refresh = RefreshToken.for_user(staff_user)
    yield str(refresh.access_token)


@pytest.fixture
def consultation(non_staff_user):
    _consultation = ConsultationFactory(
        title="My First Consultation",
        code="my-first-consultation",
        stage=Consultation.Stage.SETUP,
    )
    _consultation.users.add(non_staff_user)
    _consultation.save()
    yield _consultation
    _consultation.delete()


@pytest.fixture
def free_text_question(consultation):
    question = QuestionFactory(
        consultation=consultation, has_free_text=True, has_multiple_choice=False, number=1
    )
    yield question
    question.delete()


@pytest.fixture
def multi_choice_question(consultation):
    question = QuestionFactory(
        consultation=consultation,
        type=Question.QuestionType.CLOSED,
        has_free_text=False,
        has_multiple_choice=True,
        number=2,
    )
    yield question
    question.delete()


@pytest.fixture
def multi_choice_responses(multi_choice_question):
    """Two respondents: the first selected red and blue, the second red only."""
    respondent_1 = RespondentFactory(consultation=multi_choice_question.consultation)
    respondent_2 = RespondentFactory(consultation=multi_choice_question.consultation)
    rows = Response.objects.bulk_create(
        Response(respondent=respondent, question=multi_choice_question, text=option)
        for respondent, option in (
            (respondent_1, "red"),
            (respondent_1, "blue"),
            (respondent_2, "red"),
        )
    )
    multi_choice_question.update_response_counts()

    yield respondent_1

    Response.objects.filter(id__in=[row.id for row in rows]).delete()


@pytest.fixture()
def theme_a(free_text_question, staff_user):
    theme = SelectedThemeFactory(
        question=free_text_question,
        name="Theme A",
        key="A",
        last_modified_by=staff_user,
        version=2,
    )
    yield theme
    theme.delete()


@pytest.fixture()
def theme_b(free_text_question, staff_user):
    theme = SelectedThemeFactory(
        question=free_text_question, name="Theme B", key="B", last_modified_by=staff_user
    )
    yield theme
    theme.delete()


@pytest.fixture()
def theme_c(free_text_question, staff_user):
    theme = SelectedThemeFactory(
        question=free_text_question, name="Theme C", key=None, last_modified_by=staff_user
    )
    yield theme
    theme.delete()


@pytest.fixture()
def candidate_theme(free_text_question):
    theme = CandidateThemeFactory(question=free_text_question)
    yield theme
    theme.delete()


@pytest.fixture()
def selected_candidate_theme(free_text_question, theme_a):
    theme = CandidateThemeFactory(question=free_text_question, selectedtheme=theme_a)
    yield theme
    theme.delete()


@pytest.fixture()
def individual_demographic(consultation):
    demographic = DemographicOption.objects.create(
        consultation=consultation,
        field_name="individual",
        field_value=True,
    )
    yield demographic
    demographic.delete()


@pytest.fixture()
def northern_demographic(consultation):
    demographic = DemographicOption.objects.create(
        consultation=consultation,
        field_name="region",
        field_value="north",
    )
    yield demographic
    demographic.delete()


@pytest.fixture()
def group_demographic(consultation):
    demographic = DemographicOption.objects.create(
        consultation=consultation,
        field_name="individual",
        field_value=False,
    )
    yield demographic
    demographic.delete()


@pytest.fixture()
def southern_demographic(consultation):
    demographic = DemographicOption.objects.create(
        consultation=consultation,
        field_name="region",
        field_value="south",
    )
    yield demographic
    demographic.delete()


@pytest.fixture()
def individual_demographic_option(consultation):
    demographic_option = DemographicOption.objects.create(
        consultation=consultation, field_name="individual", field_value=True
    )
    yield demographic_option
    demographic_option.delete()


@pytest.fixture()
def group_demographic_option(consultation):
    do = DemographicOption.objects.create(
        consultation=consultation, field_name="individual", field_value=False
    )
    yield do
    do.delete()


@pytest.fixture()
def no_disability_demographic_option(consultation):
    demographic_option = DemographicOption.objects.create(
        consultation=consultation, field_name="has_disability", field_value=False
    )
    yield demographic_option
    demographic_option.delete()


@pytest.fixture()
def north_demographic_option(consultation):
    demographic_option = DemographicOption.objects.create(
        consultation=consultation, field_name="region", field_value="north"
    )
    yield demographic_option
    demographic_option.delete()


@pytest.fixture()
def south_demographic_option(consultation):
    do = DemographicOption.objects.create(
        consultation=consultation, field_name="region", field_value="south"
    )
    yield do
    do.delete()


@pytest.fixture()
def twenty_five_demographic_option(consultation):
    demographic_option = DemographicOption.objects.create(
        consultation=consultation, field_name="age_group", field_value="25-34"
    )
    yield demographic_option
    demographic_option.delete()


@pytest.fixture
def respondent_1(consultation, individual_demographic):
    respondent = Respondent.objects.create(consultation=consultation, themefinder_id=1)
    respondent.demographics.add(individual_demographic)
    yield respondent
    respondent.delete()


@pytest.fixture
def respondent_2(consultation, northern_demographic):
    respondent = Respondent.objects.create(consultation=consultation, themefinder_id=2)
    respondent.demographics.add(northern_demographic)
    yield respondent
    respondent.delete()


@pytest.fixture
def respondent_3(consultation):
    respondent = Respondent.objects.create(consultation=consultation, themefinder_id=3)
    yield respondent
    respondent.delete()


@pytest.fixture
def respondent_4(consultation):
    respondent = Respondent.objects.create(consultation=consultation, themefinder_id=4)
    yield respondent
    respondent.delete()


@pytest.fixture
def free_text_response(free_text_question, respondent_1):
    response = Response.objects.create(
        question=free_text_question, respondent=respondent_1, free_text="test response"
    )
    yield response
    response.delete()


@pytest.fixture
def another_response(free_text_question, respondent_2):
    response = Response.objects.create(
        question=free_text_question, respondent=respondent_2, free_text="i agree"
    )
    yield response
    response.delete()


@pytest.fixture
def ai_assigned_theme(free_text_question):
    theme = SelectedTheme.objects.create(question=free_text_question, key="AI assigned theme A")
    yield theme
    theme.delete()


@pytest.fixture
def free_text_annotation(free_text_response, staff_user, ai_assigned_theme):
    annotation = ResponseAnnotation.objects.create(response=free_text_response, evidence_rich=True)
    theme_b = SelectedTheme.objects.create(
        question=free_text_response.question, key="Human assigned theme B"
    )
    annotation_a = ResponseAnnotationTheme.objects.create(
        response_annotation=annotation, theme=ai_assigned_theme, assigned_by=None
    )
    annotation_b = ResponseAnnotationTheme.objects.create(
        response_annotation=annotation, theme=theme_b, assigned_by=staff_user
    )
    yield annotation
    annotation_a.delete()
    annotation_b.delete()
    theme_b.delete()
    annotation.delete()


@pytest.fixture
def human_reviewed_annotation(another_response, theme_b):
    annotation = ResponseAnnotation.objects.create(
        response=another_response, evidence_rich=True, human_reviewed=False
    )
    annotation_a = ResponseAnnotationTheme.objects.create(
        response_annotation=annotation, theme=theme_b
    )
    yield annotation
    annotation_a.delete()
    annotation.delete()


@pytest.fixture
def un_reviewed_annotation(another_response, theme_b):
    annotation = ResponseAnnotation.objects.create(
        response=another_response, evidence_rich=True, human_reviewed=True
    )
    annotation_a = ResponseAnnotationTheme.objects.create(
        response_annotation=annotation, theme=theme_b
    )
    yield annotation
    annotation_a.delete()
    annotation.delete()


@pytest.fixture
def alternative_theme(free_text_response):
    theme = SelectedTheme.objects.create(
        question=free_text_response.question, key="Human assigned theme C"
    )
    yield theme
    theme.delete()


@pytest.fixture
def embedded_responses():
    with open("./tests/examples/response_search_embeddings.yml", "r") as file:
        data = yaml.safe_load(file)

    question = QuestionFactory(text=data["question"], has_free_text=True)

    for response_data in data["responses"]:
        respondent = RespondentFactory(consultation=question.consultation)
        response = ResponseFactory(
            question=question,
            respondent=respondent,
            free_text=response_data["text"],
            embedding=response_data["embedding"],
        )
        response.search_vector = SearchVector("free_text")
        response.save()

    yield {
        "consultation_id": question.consultation.id,
        "question_id": question.id,
        "search_mode": data["search_mode"],
    }
    Consultation.objects.filter(id=question.consultation.id).delete()


@pytest.fixture
def legacy_consultation():
    """A v1-shaped consultation: a closed question with options selected through
    chosen_options and no typed questions, as the pre-v2 pipeline left them."""
    consultation = factories.ConsultationFactory(is_v1=True)
    question = factories.QuestionFactory(
        consultation=consultation, number=1, has_free_text=False, has_multiple_choice=True
    )
    red = factories.MultiChoiceAnswerFactory(question=question, text="Red")
    blue = factories.MultiChoiceAnswerFactory(question=question, text="Blue")
    for options in ([red, blue], [red]):
        response = factories.ResponseFactory(
            question=question,
            respondent=factories.RespondentFactory(consultation=consultation),
            free_text=None,
        )
        response.chosen_options.add(*options)
    return consultation


@pytest.fixture
def closed_answers(consultation):
    """A hybrid (open question with a closed sibling), a demographic question and an
    untyped legacy question, with three respondents: one multi-select, one single, one silent."""
    closed_question = factories.ClosedQuestionFactory(consultation=consultation, number=11)
    open_question = factories.OpenQuestionFactory(
        consultation=consultation, number=12, closed_question=closed_question
    )
    demographic_question = factories.DemographicQuestionFactory(
        consultation=consultation, number=13
    )
    legacy_question = factories.QuestionFactory(consultation=consultation, number=14)

    multi_select, single, silent = factories.RespondentFactory.create_batch(
        3, consultation=consultation
    )
    for respondent, options in [(multi_select, ["Red", "Blue"]), (single, ["Red"])]:
        for option in options:
            factories.ResponseFactory(
                question=closed_question, respondent=respondent, text=option, free_text=None
            )
    for respondent, region in [(multi_select, "North"), (single, "South"), (silent, "North")]:
        factories.ResponseFactory(
            question=demographic_question, respondent=respondent, text=region, free_text=None
        )
    for respondent in (multi_select, single, silent):
        factories.ResponseFactory(
            question=open_question, respondent=respondent, text="Because", free_text="Because"
        )

    return SimpleNamespace(
        closed_question=closed_question,
        open_question=open_question,
        demographic_question=demographic_question,
        legacy_question=legacy_question,
        multi_select=multi_select,
        single=single,
        silent=silent,
    )
