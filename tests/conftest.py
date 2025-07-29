import json

import boto3
import pytest
from moto import mock_aws

from consultation_analyser.factories import UserFactory


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


@pytest.fixture
def user():
    return UserFactory()
