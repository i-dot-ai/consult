import pytest

from consultation_analyser.consultations.models import ResponseAnnotation
from consultation_analyser.support_console.file_models import DetailDetection, SentimentRecord


@pytest.mark.parametrize(
    ("raw_json", "expected_output"),
    [
        (
            '{"themefinder_id":1,"evidence_rich":"NO"}',
            {"themefinder_id": 1, "evidence_rich": "NO", "evidence_rich_bool": False},
        ),
        (
            '{"themefinder_id":2,"evidence_rich":"YES"}',
            {"themefinder_id": 2, "evidence_rich": "YES", "evidence_rich_bool": True},
        ),
        (
            '{"themefinder_id":3,"evidence_rich":null}',
            {
                "themefinder_id": 3,
                "evidence_rich": "NO",
                "evidence_rich_bool": False,
            },
        ),
    ],
)
def test_DetailDetection(raw_json, expected_output):
    obj = DetailDetection.model_validate_json(raw_json)
    assert obj.model_dump() == expected_output


@pytest.mark.parametrize(
    ("raw_json", "expected_output"),
    [
        (
            '{"themefinder_id":1,"sentiment":"AGREEMENT"}',
            {
                "themefinder_id": 1,
                "sentiment": "AGREEMENT",
                "sentiment_enum": ResponseAnnotation.Sentiment.AGREEMENT,
            },
        ),
        (
            '{"themefinder_id":2,"sentiment":"DISAGREEMENT"}',
            {
                "themefinder_id": 2,
                "sentiment": "DISAGREEMENT",
                "sentiment_enum": ResponseAnnotation.Sentiment.DISAGREEMENT,
            },
        ),
        (
            '{"themefinder_id":3,"sentiment":"UNCLEAR"}',
            {
                "themefinder_id": 3,
                "sentiment": "UNCLEAR",
                "sentiment_enum": ResponseAnnotation.Sentiment.UNCLEAR,
            },
        ),
        (
            '{"themefinder_id":4,"sentiment":null}',
            {
                "themefinder_id": 4,
                "sentiment": "UNCLEAR",
                "sentiment_enum": ResponseAnnotation.Sentiment.UNCLEAR,
            },
        ),
    ],
)
def test_SentimentRecord(raw_json, expected_output):
    obj = SentimentRecord.model_validate_json(raw_json)
    assert obj.model_dump() == expected_output
