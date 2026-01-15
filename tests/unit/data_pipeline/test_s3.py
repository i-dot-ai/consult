from unittest.mock import Mock, patch

from consultation_analyser.data_pipeline.s3 import get_consultation_folders, get_question_folders


class TestGetQuestionFolders:
    @patch("consultation_analyser.data_pipeline.s3.boto3")
    def test_get_question_folders(self, mock_boto3):
        # Mock S3 objects
        mock_objects = [
            Mock(key="app_data/consultations/test/inputs/question_part_1/question.json"),
            Mock(key="app_data/consultations/test/inputs/question_part_1/responses.jsonl"),
            Mock(key="app_data/consultations/test/inputs/question_part_2/question.json"),
            Mock(key="app_data/consultations/test/inputs/question_part_2/responses.jsonl"),
            Mock(key="app_data/consultations/test/inputs/other_file.txt"),
        ]

        mock_bucket = Mock()
        mock_bucket.objects.filter.return_value = mock_objects
        mock_boto3.resource.return_value.Bucket.return_value = mock_bucket

        result = get_question_folders("app_data/consultations/test/inputs/", "test-bucket")

        expected = [
            "app_data/consultations/test/inputs/question_part_1/",
            "app_data/consultations/test/inputs/question_part_2/",
        ]
        assert sorted(result) == sorted(expected)


class TestGetConsultationFolders:
    @patch("consultation_analyser.data_pipeline.s3.boto3")
    @patch("consultation_analyser.data_pipeline.s3.settings")
    def test_get_consultation_folders(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        # Mock S3 objects with various paths
        mock_objects = [
            Mock(key="app_data/consultations/healthcare-2024/inputs/question_part_1/question.json"),
            Mock(
                key="app_data/consultations/healthcare-2024/outputs/sign_off/2024-01-10/clusterd_themes.json"
            ),
            Mock(
                key="app_data/consultations/transport-2024/inputs/question_part_1/responses.jsonl"
            ),
            Mock(
                key="app_data/consultations/transport-2024/outputs/mapping/2024-01-15/mapping.jsonl"
            ),
            Mock(key="app_data/consultations/education-2024/some_file.txt"),
            Mock(key="app_data/other_folder/not_consultation.txt"),  # Should be ignored
        ]

        mock_bucket = Mock()
        mock_bucket.objects.filter.return_value = mock_objects
        mock_boto3.resource.return_value.Bucket.return_value = mock_bucket

        result = get_consultation_folders()

        # Verify correct folders were extracted
        assert set(result) == {"healthcare-2024", "transport-2024", "education-2024"}
        assert len(result) == 3
