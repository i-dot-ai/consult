import json

import boto3
import pytest
from moto import mock_aws


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
        {"themefinder_id": 1, "response": "Yes, I think so."},
        {"themefinder_id": 2, "response": "Not sure about that."},
        {"themefinder_id": 3, "response": "I don't think so."},
        {"themefinder_id": 4, "response": "Maybe, but I need more info."},
    ]
    responses_jsonl_1 = "\n".join([json.dumps(response) for response in responses_1])
    responses_2 = [
        {"themefinder_id": 1, "response": "It's really fun."},
        {"themefinder_id": 3, "response": "It's goog."},
        {"themefinder_id": 4, "response": "I need more info."},
    ]
    responses_jsonl_2 = "\n".join([json.dumps(response) for response in responses_2])

    conn.Object(mock_s3_bucket, "app_data/CON1/inputs/respondents.jsonl").put(
        Body=respondents_jsonl
    )
    conn.Object(mock_s3_bucket, "app_data/CON1/inputs/question_part_1/question.json").put(
        Body=json.dumps(question_part_1)
    )
    conn.Object(mock_s3_bucket, "app_data/CON1/inputs/question_part_1/responses.jsonl").put(
        Body=responses_jsonl_1
    )
    conn.Object(mock_s3_bucket, "app_data/CON1/inputs/question_part_2/question.json").put(
        Body=json.dumps(question_part_2)
    )
    conn.Object(mock_s3_bucket, "app_data/CON1/inputs/question_part_2/responses.jsonl").put(
        Body=responses_jsonl_2
    )
