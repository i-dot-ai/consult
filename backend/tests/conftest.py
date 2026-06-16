import pytest
import yaml
from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.test import RequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import (
    Consultation,
    DemographicOption,
    MultiChoiceAnswer,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    SelectedTheme,
)
from factories import (
    CandidateThemeFactory,
    ConsultationFactory,
    MultiChoiceAnswerFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
    SelectedThemeFactory,
    UserFactory,
)


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
    _consultation = ConsultationFactory(title="My First Consultation", code="my-first-consultation")
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
        consultation=consultation, has_free_text=False, has_multiple_choice=True, number=2
    )
    for answer in ["red", "blue", "green"]:
        MultiChoiceAnswerFactory.create(question=question, text=answer)
    yield question
    question.delete()


@pytest.fixture
def multi_choice_responses(multi_choice_question):
    red = multi_choice_question.multichoiceanswer_set.get(
        question=multi_choice_question, text="red"
    )
    blue = multi_choice_question.multichoiceanswer_set.get(
        question=multi_choice_question, text="blue"
    )

    respondent_1 = RespondentFactory(consultation=multi_choice_question.consultation)
    response_1 = Response.objects.create(respondent=respondent_1, question=multi_choice_question)
    response_1.chosen_options.add(red)
    response_1.chosen_options.add(blue)
    response_1.save()

    respondent_2 = RespondentFactory(consultation=multi_choice_question.consultation)
    response_2 = Response.objects.create(respondent=respondent_2, question=multi_choice_question)
    response_2.chosen_options.add(red)
    response_2.save()

    # Update denormalised counts
    MultiChoiceAnswer.update_response_counts(multi_choice_question)
    multi_choice_question.update_response_counts()

    yield respondent_1

    response_1.delete()
    response_2.delete()


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


@pytest.fixture(scope="session")
def minio_client():
    """
    Session-scoped MinIO S3 client for tests.

    Provides a boto3 S3 client configured to connect to MinIO (via get_s3_client).
    The client is created once per test session and reused across all tests.

    Returns:
        boto3.client: S3 client configured for MinIO endpoint
    """
    from consultations.utils import s3 as s3_utils
    client = s3_utils.get_s3_client()
    return client


@pytest.fixture
def minio_test_bucket(minio_client):
    """
    Function-scoped fixture that ensures the test bucket exists.

    The bucket name comes from settings.AWS_BUCKET_NAME (loaded from .env.test).
    The bucket is automatically created by app startup in config.py if it doesn't exist,
    so this fixture just yields the bucket name.

    Note: Individual tests are responsible for creating and cleaning up their
    own S3 objects. This fixture only ensures the bucket exists.

    Yields:
        str: The name of the test bucket (from settings.AWS_BUCKET_NAME)
    """

    bucket_name = settings.AWS_BUCKET_NAME

    # Bucket is already created by get_s3_client() for TEST environment
    # Just yield the name for tests to use
    yield bucket_name

    # Note: No cleanup here - tests handle their own object cleanup
