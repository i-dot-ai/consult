import pytest

from boto3_client import get_s3_client
from data_pipeline.s3 import get_consultation_folders, get_question_folders


@pytest.mark.django_db
class TestGetQuestionFolders:
    def test_get_question_folders(self, s3_bucket):
        """Test getting question folders from real MinIO"""
        s3_client = get_s3_client()
        
        # Create test files in MinIO
        test_files = [
            "app_data/consultations/test/inputs/question_part_1/question.json",
            "app_data/consultations/test/inputs/question_part_1/responses.jsonl",
            "app_data/consultations/test/inputs/question_part_2/question.json",
            "app_data/consultations/test/inputs/question_part_2/responses.jsonl",
            "app_data/consultations/test/inputs/other_file.txt",
        ]
        
        for key in test_files:
            s3_client.put_object(Bucket=s3_bucket, Key=key, Body="test content")
        
        result = get_question_folders("app_data/consultations/test/inputs/", s3_bucket)
        
        expected = [
            "app_data/consultations/test/inputs/question_part_1/",
            "app_data/consultations/test/inputs/question_part_2/",
        ]
        assert sorted(result) == sorted(expected)


@pytest.mark.django_db
class TestGetConsultationFolders:
    def test_get_consultation_folders(self, s3_bucket):
        """Test getting consultation folders from real MinIO"""
        s3_client = get_s3_client()
        
        # Create test files in MinIO
        test_files = [
            "app_data/consultations/healthcare-2024/inputs/question_part_1/question.json",
            "app_data/consultations/healthcare-2024/outputs/sign_off/2024-01-10/clusterd_themes.json",
            "app_data/consultations/transport-2024/inputs/question_part_1/responses.jsonl",
            "app_data/consultations/transport-2024/outputs/mapping/2024-01-15/mapping.jsonl",
            "app_data/consultations/education-2024/some_file.txt",
            "app_data/other_folder/not_consultation.txt",  # Should be ignored
        ]
        
        for key in test_files:
            s3_client.put_object(Bucket=s3_bucket, Key=key, Body="test content")
        
        result = get_consultation_folders()
        
        # Verify correct folders were extracted
        assert set(result) == {"healthcare-2024", "transport-2024", "education-2024"}
        assert len(result) == 3
