from unittest.mock import Mock, patch

import pytest

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    SelectedTheme,
)
from consultation_analyser.data_pipeline.sync.selected_themes import export_selected_themes_to_s3


@pytest.mark.django_db
class TestExportSelectedThemesToS3:
    @patch("consultation_analyser.data_pipeline.sync.selected_themes.boto3")
    @patch("consultation_analyser.data_pipeline.sync.selected_themes.settings")
    def test_export_selected_themes_to_s3(self, mock_settings, mock_boto3):
        """Test successful export of selected themes to S3"""

        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = Mock()
        mock_boto3.client.return_value = mock_s3_client

        # Create test data with two free text questions and one multiple choice
        consultation = Consultation.objects.create(title="Test Consultation", code="test-code")
        question1 = Question.objects.create(consultation=consultation, number=1, has_free_text=True)
        Question.objects.create(consultation=consultation, number=2, has_free_text=False)
        question3 = Question.objects.create(consultation=consultation, number=3, has_free_text=True)

        # Create selected themes for both free text questions
        SelectedTheme.objects.create(
            question=question1, name="Theme 1A", description="Description 1A", key="A"
        )
        SelectedTheme.objects.create(
            question=question1, name="Theme 1B", description="Description 1B", key="B"
        )
        SelectedTheme.objects.create(
            question=question3, name="Theme 3A", description="Description 3A", key="A"
        )

        questions_exported = export_selected_themes_to_s3(consultation)

        # Verify export was called for two questions (only free text questions)
        assert questions_exported == 2
        assert mock_s3_client.put_object.call_count == 2

        # Verify correct S3 paths were used
        calls = mock_s3_client.put_object.call_args_list
        assert any("question_part_1/themes.csv" in call.kwargs["Key"] for call in calls), (
            "Question 1 themes should be exported"
        )
        assert any("question_part_3/themes.csv" in call.kwargs["Key"] for call in calls), (
            "Question 3 themes should be exported"
        )
