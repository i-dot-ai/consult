from unittest.mock import patch

import pytest
from backend.consultations.models import CandidateTheme
from backend.data_pipeline.sync.candidate_themes import (
    import_candidate_themes_from_s3,
)
from backend.factories import ConsultationFactory, QuestionFactory


@pytest.mark.django_db
class TestImportCandidateThemesFromS3:
    @patch("backend.data_pipeline.sync.candidate_themes.s3")
    @patch("backend.data_pipeline.sync.candidate_themes.settings")
    def test_import_candidate_themes_from_s3(self, mock_settings, mock_s3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        # Create test consultation and questions
        consultation = ConsultationFactory(code="test-consultation")
        question1 = QuestionFactory(consultation=consultation, number=1, text="Question 1?")
        question2 = QuestionFactory(consultation=consultation, number=2, text="Question 2?")

        # Mock S3 response with theme data for each question
        def mock_read_json(bucket_name, key, s3_client=None, raise_if_missing=True):
            if "question_part_1" in key:
                return {
                    "theme_nodes": [
                        {
                            "topic_id": "1",
                            "topic_label": "Theme A",
                            "topic_description": "Description A",
                            "source_topic_count": 10,
                            "parent_id": "0",
                            "children": [],
                        },
                        {
                            "topic_id": "2",
                            "topic_label": "Theme B",
                            "topic_description": "Description B",
                            "source_topic_count": 5,
                            "parent_id": "1",
                            "children": [],
                        },
                    ]
                }
            elif "question_part_2" in key:
                return {
                    "theme_nodes": [
                        {
                            "topic_id": "3",
                            "topic_label": "Theme C",
                            "topic_description": "Description C",
                            "source_topic_count": 8,
                            "parent_id": "0",
                            "children": [],
                        },
                    ]
                }
            return None

        mock_s3.read_json.side_effect = mock_read_json

        # Run the import
        import_candidate_themes_from_s3(
            consultation_code="test-consultation",
            timestamp="2026-01-13",
        )

        # Verify candidate themes were created
        assert CandidateTheme.objects.filter(question=question1).count() == 2
        assert CandidateTheme.objects.filter(question=question2).count() == 1

        # Verify theme data
        theme_a = CandidateTheme.objects.get(question=question1, name="Theme A")
        assert theme_a.description == "Description A"
        assert theme_a.approximate_frequency == 10
        assert theme_a.parent is None

        theme_b = CandidateTheme.objects.get(question=question1, name="Theme B")
        assert theme_b.parent == theme_a

        # Verify consultation timestamp was updated
        consultation.refresh_from_db()
        assert consultation.timestamp == "2026-01-13"
