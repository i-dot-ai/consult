import pytest

from boto3_client import get_s3_client
from consultations.models import SelectedTheme
from data_pipeline.sync.selected_themes import export_selected_themes_to_s3
from factories import ConsultationFactory, QuestionFactory


@pytest.mark.django_db
class TestExportSelectedThemesToS3:
    def test_export_selected_themes_to_s3(self, s3_bucket):
        """Test exporting selected themes to real MinIO"""
        s3_client = get_s3_client()
        
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
        
        # Verify files were actually uploaded to MinIO
        response = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix="app_data/consultations/test-code/inputs/")
        assert 'Contents' in response
        keys = [obj['Key'] for obj in response['Contents']]
        
        # Check both question files exist
        assert any("question_part_1/themes.csv" in key for key in keys)
        assert any("question_part_3/themes.csv" in key for key in keys)
        
        # Verify uploaded themes.csv content for question 1
        q1_key = next(k for k in keys if "question_part_1/themes.csv" in k)
        q1_obj = s3_client.get_object(Bucket=s3_bucket, Key=q1_key)
        q1_csv_content = q1_obj['Body'].read().decode('utf-8')
        assert "Theme Name,Theme Description" in q1_csv_content
        assert "Theme 1A,Description 1A" in q1_csv_content
        assert "Theme 1B,Description 1B" in q1_csv_content

        # Verify uploaded themes.csv content for question 3
        q3_key = next(k for k in keys if "question_part_3/themes.csv" in k)
        q3_obj = s3_client.get_object(Bucket=s3_bucket, Key=q3_key)
        q3_csv_content = q3_obj['Body'].read().decode('utf-8')
        assert "Theme Name,Theme Description" in q3_csv_content
        assert "Theme 3A,Description 3A" in q3_csv_content
