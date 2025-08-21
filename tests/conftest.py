import json

import boto3
import pytest
from django.contrib.auth.models import Group
from django.test import RequestFactory
from moto import mock_aws
from rest_framework_simplejwt.tokens import RefreshToken

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.models import (
    DemographicOption,
    Respondent,
    Response,
    ResponseAnnotation,
    ResponseAnnotationTheme,
    Theme,
)
from consultation_analyser.factories import (
    ConsultationFactory,
    MultiChoiceAnswerFactory,
    QuestionFactory,
    RespondentFactory,
    ThemeFactory,
    UserFactory,
)


@pytest.fixture()
def request_factory():
    return RequestFactory()


@pytest.fixture
def mock_s3_bucket():
    with mock_aws():
        conn = boto3.resource("s3", region_name="us-east-1")
        bucket_name = "test-bucket"
        conn.create_bucket(Bucket=bucket_name)
        yield bucket_name


@pytest.fixture
def mock_consultation_input_objects(mock_s3_bucket):
    conn = boto3.resource("s3", region_name="us-east-1")
    question_part_1 = {
        "question_text": "Do you agree?",
        "question_part_text": "Please give more details.",
        "question_number": 2,
        "question_part_number": 1,
        "question_part_type": "free_text",
    }
    question_part_2 = {
        "question_text": "Why do you like it?",
        "question_part_text": "Please comment",
        "question_number": 3,
        "question_part_number": 1,
        "question_part_type": "free_text",
    }

    respondents = [
        {"themefinder_id": 1},
        {"themefinder_id": 2},
        {"themefinder_id": 3},
        {"themefinder_id": 4},
        {"themefinder_id": 5},
    ]
    respondents_jsonl = "\n".join([json.dumps(respondent) for respondent in respondents])

    responses_1 = [
        {"themefinder_id": 1, "text": "Yes, I think so."},
        {"themefinder_id": 2, "text": "Not sure about that."},
        {"themefinder_id": 3, "text": "I don't think so."},
        {"themefinder_id": 4, "text": "Maybe, but I need more info."},
    ]
    responses_jsonl_1 = "\n".join([json.dumps(response) for response in responses_1])
    responses_2 = [
        {"themefinder_id": 1, "text": "It's really fun."},
        {"themefinder_id": 3, "text": "It's goog."},
        {"themefinder_id": 4, "text": "I need more info."},
    ]
    responses_jsonl_2 = "\n".join([json.dumps(response) for response in responses_2])

    themes = [
        {"theme_key": "A", "theme_name": "Theme A", "theme_description": "A description"},
        {"theme_key": "B", "theme_name": "Theme B", "theme_description": "B description"},
        {"theme_key": "C", "theme_name": "Theme C", "theme_description": "C description"},
    ]

    theme_mappings = [
        {"themefinder_id": 1, "theme_keys": ["A"]},
        {"themefinder_id": 2, "theme_keys": ["B"]},
        {"themefinder_id": 4, "theme_keys": ["A", "B"]},
    ]
    theme_mappings_jsonl = "\n".join(
        [json.dumps(theme_mapping) for theme_mapping in theme_mappings]
    )

    theme_mappings_2 = [
        {"themefinder_id": 1, "theme_keys": ["B"]},
        {"themefinder_id": 3, "theme_keys": ["B"]},
        {"themefinder_id": 4, "theme_keys": ["A", "B"]},
    ]
    theme_mappings_2_jsonl = "\n".join(
        [json.dumps(theme_mapping) for theme_mapping in theme_mappings_2]
    )

    sentiment_mappings = [
        {"themefinder_id": 1, "sentiment": "AGREEMENT"},
        {"themefinder_id": 2, "sentiment": "DISAGREEMENT"},
        {"themefinder_id": 4, "sentiment": "UNCLEAR"},
    ]
    sentiment_mappings_jsonl = "\n".join(
        [json.dumps(sentiment_mapping) for sentiment_mapping in sentiment_mappings]
    )

    sentiment_mappings_2 = [
        {"themefinder_id": 1, "sentiment": "AGREEMENT"},
        {"themefinder_id": 3, "sentiment": "DISAGREEMENT"},
        {"themefinder_id": 4, "sentiment": "UNCLEAR"},
    ]
    sentiment_mappings_2_jsonl = "\n".join(
        [json.dumps(sentiment_mapping) for sentiment_mapping in sentiment_mappings_2]
    )

    evidence_rich_mappings = [
        {"themefinder_id": 1, "evidence_rich": "YES"},
        {"themefinder_id": 2, "evidence_rich": "NO"},
        {"themefinder_id": 4, "evidence_rich": "YES"},
    ]
    evidence_rich_mappings_jsonl = "\n".join(
        [json.dumps(evidence_rich_mapping) for evidence_rich_mapping in evidence_rich_mappings]
    )

    evidence_rich_mappings_2 = [
        {"themefinder_id": 1, "evidence_rich": "YES"},
        {"themefinder_id": 3, "evidence_rich": "NO"},
        {"themefinder_id": 4, "evidence_rich": "YES"},
    ]
    evidence_rich_mappings_2_jsonl = "\n".join(
        [json.dumps(evidence_rich_mapping) for evidence_rich_mapping in evidence_rich_mappings_2]
    )

    conn.Object(mock_s3_bucket, "app_data/consultations/con1/inputs/respondents.jsonl").put(
        Body=respondents_jsonl
    )
    conn.Object(
        mock_s3_bucket, "app_data/consultations/con1/inputs/question_part_1/question.json"
    ).put(Body=json.dumps(question_part_1))
    conn.Object(
        mock_s3_bucket, "app_data/consultations/con1/inputs/question_part_1/responses.jsonl"
    ).put(Body=responses_jsonl_1)
    conn.Object(
        mock_s3_bucket, "app_data/consultations/con1/inputs/question_part_2/question.json"
    ).put(Body=json.dumps(question_part_2))
    conn.Object(
        mock_s3_bucket, "app_data/consultations/con1/inputs/question_part_2/responses.jsonl"
    ).put(Body=responses_jsonl_2)
    conn.Object(
        mock_s3_bucket,
        "app_data/consultations/con1/outputs/mapping/2025-04-01/question_part_1/themes.json",
    ).put(Body=json.dumps(themes))
    conn.Object(
        mock_s3_bucket,
        "app_data/consultations/con1/outputs/mapping/2025-04-01/question_part_2/themes.json",
    ).put(Body=json.dumps(themes))
    conn.Object(
        mock_s3_bucket,
        "app_data/consultations/con1/outputs/mapping/2025-04-01/question_part_1/mapping.jsonl",
    ).put(Body=theme_mappings_jsonl)
    conn.Object(
        mock_s3_bucket,
        "app_data/consultations/con1/outputs/mapping/2025-04-01/question_part_2/mapping.jsonl",
    ).put(Body=theme_mappings_2_jsonl)
    conn.Object(
        mock_s3_bucket,
        "app_data/consultations/con1/outputs/mapping/2025-04-01/question_part_1/sentiment.jsonl",
    ).put(Body=sentiment_mappings_jsonl)
    conn.Object(
        mock_s3_bucket,
        "app_data/consultations/con1/outputs/mapping/2025-04-01/question_part_2/sentiment.jsonl",
    ).put(Body=sentiment_mappings_2_jsonl)
    conn.Object(
        mock_s3_bucket,
        "app_data/consultations/con1/outputs/mapping/2025-04-01/question_part_1/detail_detection.jsonl",
    ).put(Body=evidence_rich_mappings_jsonl)
    conn.Object(
        mock_s3_bucket,
        "app_data/consultations/con1/outputs/mapping/2025-04-01/question_part_2/detail_detection.jsonl",
    ).put(Body=evidence_rich_mappings_2_jsonl)


@pytest.fixture()
def dashboard_access_group():
    group, _ = Group.objects.get_or_create(name=DASHBOARD_ACCESS)
    yield group
    group.delete()


@pytest.fixture
def non_dashboard_user():
    user = UserFactory()
    yield user
    user.delete()


@pytest.fixture
def dashboard_user(dashboard_access_group):
    user = UserFactory()
    user.groups.add(dashboard_access_group)
    user.save()
    yield user
    user.delete()


@pytest.fixture()
def user_without_consultation_access(dashboard_access_group):
    """User with dashboard access but not consultation access"""
    user = UserFactory()
    user.groups.add(dashboard_access_group)
    user.save()
    yield user
    user.delete()


@pytest.fixture
def non_consultation_user():
    user = UserFactory()
    yield user
    user.delete()


@pytest.fixture
def consultation_user_token(consultation_user):
    refresh = RefreshToken.for_user(consultation_user)
    yield str(refresh.access_token)


@pytest.fixture
def dashboard_user_token(dashboard_user):
    refresh = RefreshToken.for_user(dashboard_user)
    yield str(refresh.access_token)


@pytest.fixture
def non_consultation_user_token(non_consultation_user):
    refresh = RefreshToken.for_user(non_consultation_user)
    yield str(refresh.access_token)


@pytest.fixture
def non_dashboard_user_token(non_dashboard_user):
    refresh = RefreshToken.for_user(non_dashboard_user)
    yield str(refresh.access_token)


@pytest.fixture
def consultation(dashboard_user, non_dashboard_user):
    _consultation = ConsultationFactory(title="My First Consultation", slug="my-first-consultation")
    _consultation.users.add(dashboard_user)
    _consultation.users.add(non_dashboard_user)
    _consultation.save()
    yield _consultation
    _consultation.delete()


@pytest.fixture
def free_text_question(consultation):
    question = QuestionFactory(
        consultation=consultation, has_free_text=True, has_multiple_choice=False
    )
    yield question
    question.delete()


@pytest.fixture
def multi_choice_question(consultation):
    question = QuestionFactory(
        consultation=consultation, has_free_text=False, has_multiple_choice=True
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

    yield respondent_1

    response_1.delete()
    response_2.delete()


@pytest.fixture()
def theme_a(free_text_question):
    theme = ThemeFactory(question=free_text_question, name="Theme A", key="A")
    yield theme
    theme.delete()


@pytest.fixture()
def theme_b(free_text_question):
    theme = ThemeFactory(question=free_text_question, name="Theme B", key="B")
    yield theme
    theme.delete()


@pytest.fixture()
def consultation_user(consultation, dashboard_access_group):
    user = UserFactory()
    user.groups.add(dashboard_access_group)
    user.save()
    consultation.users.add(user)
    yield user
    user.delete()


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
def respondent_1(consultation):
    respondent = Respondent.objects.create(consultation=consultation, themefinder_id=1)
    yield respondent
    respondent.delete()

@pytest.fixture
def respondent_2(consultation):
    respondent = Respondent.objects.create(consultation=consultation, themefinder_id=2)
    yield respondent
    respondent.delete()


@pytest.fixture
def free_text_response(free_text_question, respondent_1):
    response = Response.objects.create(question=free_text_question, respondent=respondent_1)

    yield response
    response.delete()


@pytest.fixture
def free_text_annotation(free_text_response):
    annotation = ResponseAnnotation.objects.create(response=free_text_response, evidence_rich=True)
    theme_a = Theme.objects.create(question=free_text_response.question, key="A")
    annotation_a = ResponseAnnotationTheme.objects.create(
        response_annotation=annotation, theme=theme_a
    )
    yield annotation
    annotation_a.delete()
    theme_a.delete()
    annotation.delete()


@pytest.fixture
def alternative_theme(free_text_response):
    theme = Theme.objects.create(question=free_text_response.question, key="B")
    yield theme
    theme.delete()
