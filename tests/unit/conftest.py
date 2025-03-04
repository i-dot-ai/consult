import json

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def refined_themes():
    refined_themes = [
        {
            "A": "Fair Trade Certification: Ensuring ethical sourcing and supporting sustainable farming practises by requiring fair trade certification for all chocolate products."
        },
        {
            "B": "Sugar and Portion Sizing: Addressing public health concerns by reducing sugar content and implementing stricter portion size regulations for chocolate bars."
        },
        {
            "C": "Transparent Labelling: Improving transparency by mandating clear and comprehensive labelling of ingredients, nutritional information, and potential allergens."
        },
        {
            "D": "Environmental Impact: Introducing measures to minimise the environmental impact of chocolate production, such as reducing packaging waste and promoting eco-friendly practises."
        },
        {"E": "No theme: whatever the description of no theme is"},
    ]
    return refined_themes


@pytest.fixture
def mapping():
    mapping = [
        {
            "response_id": 0,
            "response": "Implementing stricter portion size regulations for chocolate bars could help promote healthier eating habits and address obesity concerns.",
            "position": "agreement",
            "reasons": [
                "The response suggests that regulating portion sizes could encourage moderation and healthier snacking.",
            ],
            "labels": [
                "B",
            ],
            "stances": [
                "POSITIVE",
            ],
        },
        {
            "response_id": 1,
            "response": "Implementing comprehensive labelling requirements for chocolate products could overwhelm consumers with too much information.",
            "position": "disagreement",
            "reasons": [
                "The response expresses concern that detailed labelling requirements might be confusing or overwhelming for consumers.",
                "Transparent labelling aims to empower informed decisions, but could potentially have the opposite effect if not executed carefully.",
            ],
            "labels": ["C", "D"],
            "stances": ["NEGATIVE", "NEGATIVE"],
        },
        {
            "response_id": 2,
            "response": "Fair trade certification could improve the lives of cocoa farmers and promote sustainable agriculture while also increasing consumer trust in chocolate products.",
            "position": "agreement",
            "reasons": [
                "The response highlights the potential benefits of fair trade certification for cocoa farmers and the environment.",
                "It also suggests that fair trade certification could enhance consumer confidence in chocolate products.",
            ],
            "labels": ["A", "C"],
            "stances": ["POSITIVE", "NEGATIVE"],
        },
        {
            "response_id": 3,
            "response": "Strict regulations on chocolate production could lead to job losses and financial strain for small businesses in the industry.",
            "position": "disagreement",
            "reasons": [
                "Stricter rules might make it difficult for smaller companies to remain compliant and competitive.",
            ],
            "labels": ["C"],
            "stances": ["NEGATIVE"],
        },
        {
            "response_id": 4,
            "response": "Increased regulation of the chocolate industry could disproportionately impact women, who are more likely to consume these products.",
            "position": "agreement",
            "reasons": [
                "The response suggests that women might be more affected by changes in the chocolate industry due to their higher consumption rates.",
                "Regulations that raise prices or reduce availability could have a greater impact on female consumers.",
            ],
            "labels": ["A", "D"],
            "stances": ["POSITIVE", "NEGATIVE"],
        },
        {
            "response_id": 5,
            "response": "Meh.",
            "position": "unclear",
            "reasons": [
                "Response is too short",
            ],
            "labels": [
                "E",
            ],
            "stances": [""],
        },
    ]
    return mapping


@pytest.fixture
def refined_themes2():
    refined_themes = [
        {"A": "Theme A: hello."},
        {"B": "Theme B: hello again."},
        {"E": "No theme: whatever the description of no theme is"},
    ]
    return refined_themes


@pytest.fixture
def mapping2():
    mapping = [
        {
            "response_id": 0,
            "response": "Response 0.",
            "position": "agreement",
            "reasons": [
                "Reason 0.",
            ],
            "labels": [
                "A",
            ],
            "stances": [
                "POSITIVE",
            ],
        },
        {
            "response_id": 6,
            "response": "Response 6",
            "position": "disagreement",
            "reasons": [
                "Reason 6",
            ],
            "labels": ["B"],
            "stances": ["NEGATIVE"],
        },
    ]
    return mapping


@pytest.fixture
def mock_s3_bucket():
    with mock_aws():
        conn = boto3.resource("s3", region_name="us-east-1")
        bucket_name = "test-bucket"
        conn.create_bucket(Bucket=bucket_name)
        yield bucket_name


@pytest.fixture
def mock_s3_objects(mock_s3_bucket, mapping, mapping2, refined_themes, refined_themes2):
    conn = boto3.resource("s3", region_name="us-east-1")
    conn.Object(mock_s3_bucket, "folder/question_0/question.json").put(
        Body=json.dumps({"question": "What do you think?"})
    )
    conn.Object(mock_s3_bucket, "folder/question_0/updated_mapping.json").put(
        Body=json.dumps(mapping)
    )
    conn.Object(mock_s3_bucket, "folder/question_0/themes.json").put(
        Body=json.dumps(refined_themes)
    )
    conn.Object(mock_s3_bucket, "folder/question_1/question.json").put(
        Body=json.dumps({"question": "What do you think this time?"})
    )
    conn.Object(mock_s3_bucket, "folder/question_1/updated_mapping.json").put(
        Body=json.dumps(mapping2)
    )
    conn.Object(mock_s3_bucket, "folder/question_1/themes.json").put(
        Body=json.dumps(refined_themes2)
    )
