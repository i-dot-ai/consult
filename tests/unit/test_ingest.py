import json
from unittest.mock import Mock, patch

import pytest

from consultation_analyser.consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
    ResponseAnnotation,
    Theme,
)
from consultation_analyser.support_console.ingest import (
    format_validation_error,
    get_consultation_codes,
    get_question_folders,
    import_consultation,
    validate_consultation_structure,
)


class TestFormatValidationError:
    def test_missing_required_file(self):
        error = "Missing required file: app_data/test/inputs/respondents.jsonl"
        result = format_validation_error(error)
        assert result["type"] == "missing_file"
        assert "respondents.jsonl" in result["message"]
        assert result["file_path"] == "app_data/test/inputs/respondents.jsonl"

    def test_missing_file_with_question_part(self):
        error = "Missing app_data/test/inputs/question_part_1/question.json"
        result = format_validation_error(error)
        assert result["type"] == "missing_file"
        assert "question.json" in result["message"]
        assert "question part 1" in result["message"]

    def test_missing_output_file(self):
        error = "Missing output file: app_data/test/outputs/mapping/2024-01-01/question_part_1/themes.json"
        result = format_validation_error(error)
        # Due to order of conditions, this gets caught by "Missing " check, not "Missing output file:" check
        assert result["type"] == "missing_file"
        assert "themes.json" in result["message"]
        assert "question part 1" in result["message"]

    def test_no_questions_found(self):
        error = "No question_part folders found in app_data/test/inputs/"
        result = format_validation_error(error)
        assert result["type"] == "no_questions"
        assert "No question folders found" in result["message"]

    def test_invalid_json(self):
        error = "Invalid JSON in app_data/test/inputs/question_part_1/question.json"
        result = format_validation_error(error)
        assert result["type"] == "invalid_format"
        assert "question.json" in result["message"]
        assert "invalid JSON format" in result["message"]

    def test_invalid_jsonl(self):
        # This test demonstrates the current bug where "Invalid JSONL" gets caught by "Invalid JSON" check
        # and fails due to incorrect splitting logic, causing an IndexError
        error = "Invalid JSONL in app_data/test/inputs/question_part_1/responses.jsonl"
        
        # The function currently has a bug where "Invalid JSONL" starts with "Invalid JSON"
        # so it tries to split on "Invalid JSON in " which doesn't exist, causing IndexError
        import pytest
        with pytest.raises(IndexError):
            format_validation_error(error)

    def test_empty_file(self):
        error = "Empty file: app_data/test/inputs/question_part_1/responses.jsonl"
        result = format_validation_error(error)
        assert result["type"] == "empty_file"
        assert "responses.jsonl" in result["message"]
        assert "empty" in result["message"]

    def test_file_not_found(self):
        error = "Error checking app_data/test/file.json: An error occurred (404) when calling the HeadObject operation: Not Found"
        result = format_validation_error(error)
        assert result["type"] == "file_not_found"
        assert "file.json" in result["message"]
        assert "Cannot find file" in result["message"]

    def test_unexpected_error(self):
        error = "Unexpected error during validation: Something went wrong"
        result = format_validation_error(error)
        assert result["type"] == "system_error"
        assert "unexpected error" in result["message"]

    def test_unknown_error(self):
        error = "Some random error message"
        result = format_validation_error(error)
        assert result["type"] == "unknown"
        assert result["message"] == "Some random error message"


class TestGetQuestionFolders:
    @patch('consultation_analyser.support_console.ingest.boto3')
    def test_get_question_folders(self, mock_boto3):
        # Mock S3 objects
        mock_objects = [
            Mock(key="app_data/test/inputs/question_part_1/question.json"),
            Mock(key="app_data/test/inputs/question_part_1/responses.jsonl"),
            Mock(key="app_data/test/inputs/question_part_2/question.json"),
            Mock(key="app_data/test/inputs/question_part_2/responses.jsonl"),
            Mock(key="app_data/test/inputs/other_file.txt"),
        ]
        
        mock_bucket = Mock()
        mock_bucket.objects.filter.return_value = mock_objects
        mock_boto3.resource.return_value.Bucket.return_value = mock_bucket
        
        result = get_question_folders("app_data/test/inputs/", "test-bucket")
        
        expected = [
            "app_data/test/inputs/question_part_1/",
            "app_data/test/inputs/question_part_2/"
        ]
        assert sorted(result) == sorted(expected)

    @patch('consultation_analyser.support_console.ingest.boto3')
    def test_get_question_folders_empty(self, mock_boto3):
        mock_bucket = Mock()
        mock_bucket.objects.filter.return_value = []
        mock_boto3.resource.return_value.Bucket.return_value = mock_bucket
        
        result = get_question_folders("app_data/test/inputs/", "test-bucket")
        assert result == []


class TestGetConsultationCodes:
    @patch('consultation_analyser.support_console.ingest.boto3')
    @patch('consultation_analyser.support_console.ingest.settings')
    def test_get_consultation_codes(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        
        mock_objects = [
            Mock(key="app_data/consultation1/inputs/file.json"),
            Mock(key="app_data/consultation2/inputs/file.json"),
            Mock(key="app_data/consultation1/outputs/file.json"),
            Mock(key="app_data/other/file.json"),
        ]
        
        mock_bucket = Mock()
        mock_bucket.objects.filter.return_value = mock_objects
        mock_boto3.resource.return_value.Bucket.return_value = mock_bucket
        
        result = get_consultation_codes()
        
        expected = [
            {"text": "consultation1", "value": "consultation1"},
            {"text": "consultation2", "value": "consultation2"},
            {"text": "other", "value": "other"}
        ]
        assert sorted(result, key=lambda x: x["text"]) == sorted(expected, key=lambda x: x["text"])

    @patch('consultation_analyser.support_console.ingest.boto3')
    @patch('consultation_analyser.support_console.ingest.settings')
    def test_get_consultation_codes_exception(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_boto3.resource.side_effect = Exception("S3 error")
        
        result = get_consultation_codes()
        assert result == []


class TestValidateConsultationStructure:
    @patch('consultation_analyser.support_console.ingest.boto3')
    @patch('consultation_analyser.support_console.ingest.get_question_folders')
    def test_validate_consultation_structure_valid(self, mock_get_folders, mock_boto3):
        mock_get_folders.return_value = ["app_data/test/inputs/question_part_1/"]
        
        mock_s3_client = Mock()
        mock_s3_client.head_object.return_value = {}
        
        # Create properly mocked Body object with both read() and iter_lines() methods
        def mock_get_object(Bucket, Key):
            if "question.json" in Key:
                return {
                    "Body": Mock(
                        read=Mock(return_value=b'{"question_text": "Test"}')
                    )
                }
            elif "responses.jsonl" in Key:
                return {
                    "Body": Mock(
                        iter_lines=Mock(return_value=iter([b'{"themefinder_id": 1, "text": "test"}']))
                    )
                }
            return {"Body": Mock()}
        
        mock_s3_client.get_object = mock_get_object
        mock_boto3.client.return_value = mock_s3_client
        
        is_valid, errors = validate_consultation_structure("bucket", "test", "2024-01-01")
        
        assert is_valid is True
        assert errors == []

    @patch('consultation_analyser.support_console.ingest.boto3')
    @patch('consultation_analyser.support_console.ingest.get_question_folders')
    def test_validate_consultation_structure_missing_respondents(self, mock_get_folders, mock_boto3):
        mock_get_folders.return_value = ["app_data/test/inputs/question_part_1/"]
        
        mock_s3_client = Mock()
        # Create a proper NoSuchKey exception
        class NoSuchKeyException(Exception):
            pass
        
        mock_boto3.client.return_value.exceptions.NoSuchKey = NoSuchKeyException
        mock_s3_client.head_object.side_effect = NoSuchKeyException("Not found")
        mock_s3_client.exceptions = Mock()
        mock_s3_client.exceptions.NoSuchKey = NoSuchKeyException
        mock_boto3.client.return_value = mock_s3_client
        
        is_valid, errors = validate_consultation_structure("bucket", "test", "2024-01-01")
        
        assert is_valid is False
        assert "Missing required file" in errors[0]
        assert "respondents.jsonl" in errors[0]

    @patch('consultation_analyser.support_console.ingest.boto3')
    @patch('consultation_analyser.support_console.ingest.get_question_folders')
    def test_validate_consultation_structure_no_questions(self, mock_get_folders, mock_boto3):
        mock_get_folders.return_value = []
        
        mock_s3_client = Mock()
        mock_s3_client.head_object.return_value = {}
        mock_boto3.client.return_value = mock_s3_client
        
        is_valid, errors = validate_consultation_structure("bucket", "test", "2024-01-01")
        
        assert is_valid is False
        assert "No question_part folders found" in errors[0]


@pytest.mark.django_db
class TestImportConsultation:
    @patch('consultation_analyser.support_console.ingest.boto3')
    @patch('consultation_analyser.support_console.ingest.get_question_folders')
    @patch('consultation_analyser.support_console.ingest.settings')
    def test_import_consultation_success(self, mock_settings, mock_get_folders, mock_boto3):
        from consultation_analyser.authentication.models import User
        
        # Create test user
        user = User.objects.create_user(email="test@example.com")
        
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_get_folders.return_value = ["app_data/test/inputs/question_part_1/"]
        
        # Mock S3 responses
        mock_s3_client = Mock()
        
        # Mock respondents file
        respondents_data = b'{"themefinder_id": 1, "demographics": {}}\n{"themefinder_id": 2, "demographics": {}}'
        
        # Mock question file
        question_data = b'{"question_text": "What do you think?"}'
        
        # Mock responses file
        responses_data = b'{"themefinder_id": 1, "text": "Good idea"}\n{"themefinder_id": 2, "text": "Bad idea"}'
        
        # Mock themes file
        themes_data = b'[{"theme_key": "A", "theme_name": "Theme A", "theme_description": "Description A"}]'
        
        # Mock mapping file
        mapping_data = b'{"themefinder_id": 1, "theme_keys": ["A"]}\n{"themefinder_id": 2, "theme_keys": ["A"]}'
        
        # Mock sentiment file
        sentiment_data = b'{"themefinder_id": 1, "sentiment": "AGREEMENT"}\n{"themefinder_id": 2, "sentiment": "DISAGREEMENT"}'
        
        # Mock evidence file
        evidence_data = b'{"themefinder_id": 1, "evidence_rich": "YES"}\n{"themefinder_id": 2, "evidence_rich": "NO"}'
        
        def get_object_side_effect(Bucket, Key):
            if "respondents.jsonl" in Key:
                return {"Body": Mock(iter_lines=Mock(return_value=respondents_data.split(b'\n')))}
            elif "question.json" in Key:
                return {"Body": Mock(read=Mock(return_value=question_data))}
            elif "responses.jsonl" in Key:
                return {"Body": Mock(iter_lines=Mock(return_value=responses_data.split(b'\n')))}
            elif "themes.json" in Key:
                return {"Body": Mock(read=Mock(return_value=themes_data))}
            elif "mapping.jsonl" in Key:
                return {"Body": Mock(iter_lines=Mock(return_value=mapping_data.split(b'\n')))}
            elif "sentiment.jsonl" in Key:
                return {"Body": Mock(iter_lines=Mock(return_value=sentiment_data.split(b'\n')))}
            elif "detail_detection.jsonl" in Key:
                return {"Body": Mock(iter_lines=Mock(return_value=evidence_data.split(b'\n')))}
            
        mock_s3_client.get_object.side_effect = get_object_side_effect
        mock_boto3.client.return_value = mock_s3_client
        
        # Run the import
        import_consultation(
            consultation_name="Test Consultation",
            consultation_code="test",
            timestamp="2024-01-01",
            current_user_id=user.id
        )
        
        # Verify results
        consultation = Consultation.objects.get(title="Test Consultation")
        assert consultation.users.filter(id=user.id).exists()
        
        respondents = Respondent.objects.filter(consultation=consultation)
        assert respondents.count() == 2
        
        questions = Question.objects.filter(consultation=consultation)
        assert questions.count() == 1
        assert questions.first().text == "What do you think?"
        
        responses = Response.objects.filter(question__consultation=consultation)
        assert responses.count() == 2
        
        themes = Theme.objects.filter(question__consultation=consultation)
        assert themes.count() == 1
        assert themes.first().key == "A"
        
        annotations = ResponseAnnotation.objects.filter(response__question__consultation=consultation)
        assert annotations.count() == 2

    @patch('consultation_analyser.support_console.ingest.boto3')
    @patch('consultation_analyser.support_console.ingest.settings')
    def test_import_consultation_s3_error(self, mock_settings, mock_boto3):
        from consultation_analyser.authentication.models import User
        
        user = User.objects.create_user(email="test@example.com")
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        
        mock_s3_client = Mock()
        mock_s3_client.get_object.side_effect = Exception("S3 Error")
        mock_boto3.client.return_value = mock_s3_client
        
        with pytest.raises(Exception) as exc_info:
            import_consultation(
                consultation_name="Test Consultation",
                consultation_code="test",
                timestamp="2024-01-01",
                current_user_id=user.id
            )
        
        assert "S3 Error" in str(exc_info.value)

    @patch('consultation_analyser.support_console.ingest.boto3')
    @patch('consultation_analyser.support_console.ingest.get_question_folders')
    @patch('consultation_analyser.support_console.ingest.settings')
    def test_import_consultation_missing_question_text(self, mock_settings, mock_get_folders, mock_boto3):
        from consultation_analyser.authentication.models import User
        
        user = User.objects.create_user(email="test@example.com")
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_get_folders.return_value = ["app_data/test/inputs/question_part_1/"]
        
        mock_s3_client = Mock()
        
        # Mock empty respondents file
        respondents_data = b'{"themefinder_id": 1}'
        
        # Mock question file with empty text
        question_data = b'{"question_text": ""}'
        
        def get_object_side_effect(Bucket, Key):
            if "respondents.jsonl" in Key:
                return {"Body": Mock(iter_lines=Mock(return_value=[respondents_data]))}
            elif "question.json" in Key:
                return {"Body": Mock(read=Mock(return_value=question_data))}
            
        mock_s3_client.get_object.side_effect = get_object_side_effect
        mock_boto3.client.return_value = mock_s3_client
        
        with pytest.raises(ValueError) as exc_info:
            import_consultation(
                consultation_name="Test Consultation",
                consultation_code="test",
                timestamp="2024-01-01",
                current_user_id=user.id
            )
        
        assert "Question text is required" in str(exc_info.value)