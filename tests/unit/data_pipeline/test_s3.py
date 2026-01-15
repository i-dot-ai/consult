from unittest.mock import Mock, patch

from consultation_analyser.data_pipeline.s3 import get_question_folders


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
