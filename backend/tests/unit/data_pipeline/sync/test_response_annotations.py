from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError

from consultations.models import (
    ResponseAnnotation,
    SelectedTheme,
)
from data_pipeline.sync.response_annotations import (
    import_response_annotations_from_s3,
    load_detail_detections_from_s3,
    load_selected_themes_from_s3,
    load_theme_mappings_from_s3,
)
from factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
)


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "GetObject")


@pytest.mark.django_db
class TestImportResponseAnnotationsFromS3:
    @patch("data_pipeline.sync.response_annotations.s3")
    @patch("data_pipeline.sync.response_annotations.settings")
    def test_import_response_annotations_from_s3(self, mock_settings, mock_s3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        # Set up test consultation
        consultation = ConsultationFactory(code="test-consultation")
        question = QuestionFactory(
            consultation=consultation,
            number=1,
            text="What do you think?",
            has_free_text=True,
        )
        respondent1 = RespondentFactory(consultation=consultation, themefinder_id=1)
        respondent2 = RespondentFactory(consultation=consultation, themefinder_id=2)
        ResponseFactory(
            question=question,
            respondent=respondent1,
            free_text="I support this proposal",
        )
        ResponseFactory(
            question=question,
            respondent=respondent2,
            free_text="I have concerns about implementation",
        )
        theme_a = SelectedTheme.objects.create(
            question=question,
            name="Support",
            description="General support for proposal",
        )
        theme_b = SelectedTheme.objects.create(
            question=question,
            name="Concerns",
            description="Implementation concerns",
        )

        # Mock S3 responses
        mock_themes = [
            {
                "theme_key": "A",
                "theme_name": "Support",
                "theme_description": "General support for proposal",
            },
            {
                "theme_key": "B",
                "theme_name": "Concerns",
                "theme_description": "Implementation concerns",
            },
        ]

        mock_sentiments = [
            {"themefinder_id": 1, "sentiment": "AGREEMENT"},
            {"themefinder_id": 2, "sentiment": "DISAGREEMENT"},
        ]

        mock_detail_detections = [
            {"themefinder_id": 1, "evidence_rich": "YES"},
            {"themefinder_id": 2, "evidence_rich": "NO"},
        ]

        mock_mappings = [
            {"themefinder_id": 1, "theme_keys": ["A"]},
            {"themefinder_id": 2, "theme_keys": ["B"]},
        ]

        def mock_read_json(bucket_name, key, s3_client=None, raise_if_missing=True):
            if "themes.json" in key:
                return mock_themes
            return None

        def mock_read_jsonl(bucket_name, key, s3_client=None, raise_if_missing=True):
            if "sentiment.jsonl" in key:
                return mock_sentiments
            elif "detail_detection.jsonl" in key:
                return mock_detail_detections
            elif "mapping.jsonl" in key:
                return mock_mappings
            return []

        mock_s3.read_json.side_effect = mock_read_json
        mock_s3.read_jsonl.side_effect = mock_read_jsonl

        # Run the import
        import_response_annotations_from_s3(
            consultation_code="test-consultation",
            timestamp="2024-01-20",
            question_numbers=[1],
        )

        # Verify annotations were created
        assert ResponseAnnotation.objects.filter(response__question=question).count() == 2

        # Verify annotation data for respondent 1
        annotation1 = ResponseAnnotation.objects.get(response__respondent=respondent1)
        assert annotation1.sentiment == "AGREEMENT"
        assert annotation1.evidence_rich is True
        assert theme_a in annotation1.themes.all()

        # Verify annotation data for respondent 2
        annotation2 = ResponseAnnotation.objects.get(response__respondent=respondent2)
        assert annotation2.sentiment == "DISAGREEMENT"
        assert annotation2.evidence_rich is False
        assert theme_b in annotation2.themes.all()

        # Verify consultation stage was updated
        consultation.refresh_from_db()
        assert consultation.stage == consultation.Stage.ANALYSIS

        # Verify consultation timestamp was updated
        assert consultation.timestamp == "2024-01-20"

        # Verify theme keys were persisted from batch output
        theme_a.refresh_from_db()
        theme_b.refresh_from_db()
        assert theme_a.key == "A"
        assert theme_b.key == "B"


class TestLoadSelectedThemesFromS3:
    @patch("data_pipeline.sync.response_annotations.s3.read_json")
    def test_raises_value_error_when_themes_file_missing(self, mock_read_json):
        mock_read_json.side_effect = _client_error("NoSuchKey")

        with pytest.raises(ValueError) as exc_info:
            load_selected_themes_from_s3(
                consultation_code="test-code",
                question_number=1,
                timestamp="2024-01-20",
                bucket_name="test-bucket",
            )

        message = str(exc_info.value)
        assert "test-code" in message
        assert "1" in message
        assert isinstance(exc_info.value.__cause__, ClientError)

    @patch("data_pipeline.sync.response_annotations.s3.read_json")
    def test_propagates_non_missing_client_error_unchanged(self, mock_read_json):
        mock_read_json.side_effect = _client_error("AccessDenied")

        with pytest.raises(ClientError) as exc_info:
            load_selected_themes_from_s3(
                consultation_code="test-code",
                question_number=1,
                timestamp="2024-01-20",
                bucket_name="test-bucket",
            )

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"


class TestLoadDetailDetectionsFromS3:
    @patch("data_pipeline.sync.response_annotations.s3.read_jsonl")
    def test_raises_value_error_when_file_missing(self, mock_read_jsonl):
        mock_read_jsonl.side_effect = _client_error("NoSuchKey")

        with pytest.raises(ValueError) as exc_info:
            load_detail_detections_from_s3(
                consultation_code="test-code",
                question_number=2,
                timestamp="2024-01-20",
                bucket_name="test-bucket",
            )

        message = str(exc_info.value)
        assert "test-code" in message
        assert "2" in message
        assert isinstance(exc_info.value.__cause__, ClientError)

    @patch("data_pipeline.sync.response_annotations.s3.read_jsonl")
    def test_propagates_non_missing_client_error_unchanged(self, mock_read_jsonl):
        mock_read_jsonl.side_effect = _client_error("AccessDenied")

        with pytest.raises(ClientError) as exc_info:
            load_detail_detections_from_s3(
                consultation_code="test-code",
                question_number=2,
                timestamp="2024-01-20",
                bucket_name="test-bucket",
            )

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"


class TestLoadThemeMappingsFromS3:
    @patch("data_pipeline.sync.response_annotations.s3.read_jsonl")
    def test_raises_value_error_when_file_missing(self, mock_read_jsonl):
        mock_read_jsonl.side_effect = _client_error("NoSuchKey")

        with pytest.raises(ValueError) as exc_info:
            load_theme_mappings_from_s3(
                consultation_code="test-code",
                question_number=3,
                timestamp="2024-01-20",
                bucket_name="test-bucket",
            )

        message = str(exc_info.value)
        assert "test-code" in message
        assert "3" in message
        assert isinstance(exc_info.value.__cause__, ClientError)

    @patch("data_pipeline.sync.response_annotations.s3.read_jsonl")
    def test_propagates_non_missing_client_error_unchanged(self, mock_read_jsonl):
        mock_read_jsonl.side_effect = _client_error("AccessDenied")

        with pytest.raises(ClientError) as exc_info:
            load_theme_mappings_from_s3(
                consultation_code="test-code",
                question_number=3,
                timestamp="2024-01-20",
                bucket_name="test-bucket",
            )

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
