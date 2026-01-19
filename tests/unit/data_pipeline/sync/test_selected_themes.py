from unittest.mock import Mock, patch

import pytest

from backend.consultations.models import SelectedTheme
from backend.data_pipeline.sync.selected_themes import export_selected_themes_to_s3
from backend.factories import ConsultationFactory, QuestionFactory


@pytest.mark.django_db
class TestExportSelectedThemesToS3:
    @patch("backend.data_pipeline.sync.selected_themes.boto3")
    @patch("backend.data_pipeline.sync.selected_themes.settings")
    def test_export_selected_themes_to_s3(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # Create consultation, questions and selected themes
        consultation = ConsultationFactory(code="test-code")

        question1 = QuestionFactory(consultation=consultation, number=1, has_free_text=True)
        QuestionFactory(consultation=consultation, number=2, has_free_text=False)
        question3 = QuestionFactory(consultation=consultation, number=3, has_free_text=True)

        SelectedTheme.objects.create(
            question=question1, name="Theme 1A", description="Description 1A"
        )
        SelectedTheme.objects.create(
            question=question1, name="Theme 1B", description="Description 1B"
        )
        SelectedTheme.objects.create(
            question=question3, name="Theme 3A", description="Description 3A"
        )

        questions_exported = export_selected_themes_to_s3(consultation)

        # Verify export was called for two questions (only free text questions)
        assert questions_exported == 2
        assert mock_s3_client.put_object.call_count == 2

        # Verify correct S3 paths were used
        calls = mock_s3_client.put_object.call_args_list
        assert any("question_part_1/themes.csv" in call.kwargs["Key"] for call in calls)
        assert any("question_part_3/themes.csv" in call.kwargs["Key"] for call in calls)

        # Verify uploaded themes.csv content for question 1
        q1_call = next(c for c in calls if "question_part_1/themes.csv" in c.kwargs["Key"])
        q1_csv_content = q1_call.kwargs["Body"]
        assert "Theme Name,Theme Description" in q1_csv_content
        assert "Theme 1A,Description 1A" in q1_csv_content
        assert "Theme 1B,Description 1B" in q1_csv_content

        # Verify uploaded themes.csv content for question 3
        q3_call = next(c for c in calls if "question_part_3/themes.csv" in c.kwargs["Key"])
        q3_csv_content = q3_call.kwargs["Body"]
        assert "Theme Name,Theme Description" in q3_csv_content
        assert "Theme 3A,Description 3A" in q3_csv_content
