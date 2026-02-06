from unittest.mock import patch

import pytest
from backend.consultations.models import SelectedTheme, Response
from backend.data_pipeline.sync.response_annotations import (
    import_response_annotations_from_s3,
)
from backend.factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
)


@pytest.mark.django_db
class TestImportResponseAnnotationsFromS3:
    @patch("backend.data_pipeline.sync.response_annotations.s3")
    @patch("backend.data_pipeline.sync.response_annotations.settings")
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
        assert Response.objects.filter(question=question).count() == 2

        # Verify annotation data for respondent 1
        response1 = Response.objects.get(respondent=respondent1)
        assert response1.sentiment == "AGREEMENT"
        assert response1.evidence_rich is True
        assert theme_a in response1.themes.all()

        # Verify annotation data for respondent 2
        response2 = Response.objects.get(espondent=respondent2)
        assert response2.sentiment == "DISAGREEMENT"
        assert response2.evidence_rich is False
        assert theme_b in response2.themes.all()

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
