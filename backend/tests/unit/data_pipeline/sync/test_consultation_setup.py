import json
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from django.db.models import Count

from consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
)
from data_pipeline.sync.consultation_setup import (
    load_question_from_s3,
    load_respondents_from_s3,
)
from factories import UserFactory

logger = settings.LOGGER


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "GetObject")

class TestLoadRespondentsFromS3:
    @patch("data_pipeline.sync.consultation_setup.s3.read_jsonl")
    def test_raises_value_error_when_file_missing(self, mock_read_jsonl):
        mock_read_jsonl.side_effect = _client_error("NoSuchKey")

        with pytest.raises(ValueError) as exc_info:
            load_respondents_from_s3(
                consultation_code="test-code",
                bucket_name="test-bucket",
            )

        assert "respondents.jsonl" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ClientError)

    @patch("data_pipeline.sync.consultation_setup.s3.read_jsonl")
    def test_propagates_non_missing_client_error_unchanged(self, mock_read_jsonl):
        mock_read_jsonl.side_effect = _client_error("AccessDenied")

        with pytest.raises(ClientError) as exc_info:
            load_respondents_from_s3(
                consultation_code="test-code",
                bucket_name="test-bucket",
            )

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"


class TestLoadQuestionFromS3:
    @patch("data_pipeline.sync.consultation_setup.s3.read_json")
    def test_raises_value_error_when_file_missing(self, mock_read_json):
        mock_read_json.side_effect = _client_error("NoSuchKey")

        with pytest.raises(ValueError) as exc_info:
            load_question_from_s3(
                consultation_code="test-code",
                question_number=1,
                bucket_name="test-bucket",
            )

        message = str(exc_info.value)
        assert "question_part_1" in message
        assert isinstance(exc_info.value.__cause__, ClientError)

    @patch("data_pipeline.sync.consultation_setup.s3.read_json")
    def test_propagates_non_missing_client_error_unchanged(self, mock_read_json):
        mock_read_json.side_effect = _client_error("AccessDenied")

        with pytest.raises(ClientError) as exc_info:
            load_question_from_s3(
                consultation_code="test-code",
                question_number=1,
                bucket_name="test-bucket",
            )

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
