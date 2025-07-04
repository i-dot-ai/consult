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
    create_consultation,
    get_consultation_codes,
    get_question_folders,
    import_questions,
    import_respondents,
    import_response_annotations,
    import_responses,
    validate_consultation_structure,
)


def get_object_side_effect(Bucket, Key):
    # Mock respondents file
    respondents_data = b'{"themefinder_id": 1, "demographic_data": {"location": "Wales"}}\n{"themefinder_id": 2, "demographic_data": {"location": "Scotland"}}'

    # Mock question file
    question_data = b'{"question_text": "What do you think?", "has_free_text": true, "options": ["a", "b", "c"]}'

    # Mock responses file
    responses_data = b'{"themefinder_id": 1, "text": "Good idea", "chosen_options": ["a"]}\n{"themefinder_id": 2, "text": "Bad idea", "chosen_options": ["b", "c"]}'

    # Mock themes file
    themes_data = (
        b'[{"theme_key": "A", "theme_name": "Theme A", "theme_description": "Description A"}]'
    )

    # Mock mapping file
    mapping_data = (
        b'{"themefinder_id": 1, "theme_keys": ["A"]}\n{"themefinder_id": 2, "theme_keys": ["A"]}'
    )

    # Mock sentiment file
    sentiment_data = b'{"themefinder_id": 1, "sentiment": "AGREEMENT"}\n{"themefinder_id": 2, "sentiment": "DISAGREEMENT"}'

    # Mock evidence file
    evidence_data = b'{"themefinder_id": 1, "evidence_rich": "YES"}\n{"themefinder_id": 2, "evidence_rich": "NO"}'

    if "respondents.jsonl" in Key:
        return {"Body": Mock(iter_lines=Mock(return_value=respondents_data.split(b"\n")))}
    elif "question.json" in Key:
        return {"Body": Mock(read=Mock(return_value=question_data))}
    elif "responses.jsonl" in Key:
        return {"Body": Mock(iter_lines=Mock(return_value=responses_data.split(b"\n")))}
    elif "themes.json" in Key:
        return {"Body": Mock(read=Mock(return_value=themes_data))}
    elif "mapping.jsonl" in Key:
        return {"Body": Mock(iter_lines=Mock(return_value=mapping_data.split(b"\n")))}
    elif "sentiment.jsonl" in Key:
        return {"Body": Mock(iter_lines=Mock(return_value=sentiment_data.split(b"\n")))}
    elif "detail_detection.jsonl" in Key:
        return {"Body": Mock(iter_lines=Mock(return_value=evidence_data.split(b"\n")))}
    else:
        return None


class TestGetQuestionFolders:
    @patch("consultation_analyser.support_console.ingest.boto3")
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

    @patch("consultation_analyser.support_console.ingest.boto3")
    def test_get_question_folders_empty(self, mock_boto3):
        mock_bucket = Mock()
        mock_bucket.objects.filter.return_value = []
        mock_boto3.resource.return_value.Bucket.return_value = mock_bucket

        result = get_question_folders("app_data/consultations/test/inputs/", "test-bucket")
        assert result == []


class TestGetConsultationCodes:
    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_get_consultation_codes(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        mock_objects = [
            Mock(key="app_data/consultations/consultation1/inputs/file.json"),
            Mock(key="app_data/consultations/consultation2/inputs/file.json"),
            Mock(key="app_data/consultations/consultation1/outputs/file.json"),
            Mock(key="app_data/consultations/other/file.json"),
        ]

        mock_bucket = Mock()
        mock_bucket.objects.filter.return_value = mock_objects
        mock_boto3.resource.return_value.Bucket.return_value = mock_bucket

        result = get_consultation_codes()

        expected = [
            {"text": "consultation1", "value": "consultation1"},
            {"text": "consultation2", "value": "consultation2"},
            {"text": "other", "value": "other"},
        ]
        assert sorted(result, key=lambda x: x["text"]) == sorted(expected, key=lambda x: x["text"])

    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_get_consultation_codes_exception(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_boto3.resource.side_effect = Exception("S3 error")

        result = get_consultation_codes()
        assert result == []


class TestValidateConsultationStructure:
    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.get_question_folders")
    def test_validate_consultation_structure_valid(self, mock_get_folders, mock_boto3):
        mock_get_folders.return_value = ["app_data/consultations/test/inputs/question_part_1/"]

        mock_s3_client = Mock()
        mock_s3_client.head_object.return_value = {}

        # Create properly mocked Body object with both read() and iter_lines() methods
        def mock_get_object(Bucket, Key):
            if "question.json" in Key:
                return {"Body": Mock(read=Mock(return_value=b'{"question_text": "Test"}'))}
            elif "responses.jsonl" in Key:
                return {
                    "Body": Mock(
                        iter_lines=Mock(
                            return_value=iter([b'{"themefinder_id": 1, "text": "test"}'])
                        )
                    )
                }
            return {"Body": Mock()}

        mock_s3_client.get_object = mock_get_object
        mock_boto3.client.return_value = mock_s3_client

        is_valid, errors = validate_consultation_structure("bucket", "test", "2024-01-01")

        assert is_valid is True
        assert errors == []

    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.get_question_folders")
    def test_validate_consultation_structure_missing_respondents(
        self, mock_get_folders, mock_boto3
    ):
        mock_get_folders.return_value = ["app_data/consultations/test/inputs/question_part_1/"]

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

    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.get_question_folders")
    def test_validate_consultation_structure_no_questions(self, mock_get_folders, mock_boto3):
        mock_get_folders.return_value = []

        mock_s3_client = Mock()
        mock_s3_client.head_object.return_value = {}
        mock_boto3.client.return_value = mock_s3_client

        is_valid, errors = validate_consultation_structure("bucket", "test", "2024-01-01")

        assert is_valid is False
        assert "No question_part folders found" in errors[0]


@pytest.mark.django_db
class TestImportConsultationFullFlow:
    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.get_question_folders")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_import_consultation_success(self, mock_settings, mock_get_folders, mock_boto3):
        from consultation_analyser.authentication.models import User

        # Create test user
        user = User.objects.create_user(email="test@example.com")

        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_get_folders.return_value = ["app_data/consultations/test/inputs/question_part_1/"]

        # Mock S3 responses
        mock_s3_client = Mock()
        mock_s3_client.get_object.side_effect = get_object_side_effect
        mock_boto3.client.return_value = mock_s3_client

        # Run the import
        create_consultation(
            consultation_name="Test Consultation",
            consultation_code="test",
            timestamp="2024-01-01",
            current_user_id=user.id,
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

        annotations = ResponseAnnotation.objects.filter(
            response__question__consultation=consultation
        )
        assert annotations.count() == 2


@pytest.mark.django_db
class TestRespondentsImport:
    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_import_respondents(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        # Mock S3 responses
        mock_s3_client = Mock()
        mock_s3_client.get_object.side_effect = get_object_side_effect
        mock_boto3.client.return_value = mock_s3_client

        consultation = Consultation.objects.create(title="Test Consultation")
        consultation_code = "test"

        # Run the import
        import_respondents(consultation, consultation_code)

        # Verify results
        respondents = Respondent.objects.filter(consultation=consultation)
        assert respondents.count() == 2

        assert respondents.first().demographics["location"] == "Wales"
        assert respondents.last().demographics["location"] == "Scotland"

    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_import_respondents_s3_error(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        mock_s3_client = Mock()
        mock_s3_client.get_object.side_effect = Exception("S3 Error")
        mock_boto3.client.return_value = mock_s3_client

        consultation = Consultation.objects.create(title="Test Consultation")
        consultation_code = "test"

        with pytest.raises(Exception) as exc_info:
            import_respondents(consultation, consultation_code)

        assert "S3 Error" in str(exc_info.value)


@pytest.mark.django_db
class TestQuestionsImport:
    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.get_question_folders")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_import_question(self, mock_settings, mock_get_folders, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        # Mock S3 responses
        mock_s3_client = Mock()
        mock_get_folders.return_value = ["app_data/consultations/test/inputs/question_part_1/"]
        mock_s3_client.get_object.side_effect = get_object_side_effect
        mock_boto3.client.return_value = mock_s3_client

        consultation = Consultation.objects.create(title="Test Consultation")
        consultation_code = "test"
        Respondent.objects.create(consultation=consultation, themefinder_id=1)
        Respondent.objects.create(consultation=consultation, themefinder_id=2)

        # Run the import
        import_questions(
            consultation,
            consultation_code,
            "2024-01-01",
        )

        # Verify results
        questions = Question.objects.filter(consultation=consultation)
        assert questions.count() == 1
        assert questions.first().text == "What do you think?"
        assert questions.first().has_free_text
        assert questions.first().has_multiple_choice
        assert questions.first().multiple_choice_options == ["a", "b", "c"]

        themes = Theme.objects.filter(question__consultation=consultation)
        assert themes.count() == 1
        assert themes.first().key == "A"

    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.get_question_folders")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_import_questions_missing_question_text(
        self, mock_settings, mock_get_folders, mock_boto3
    ):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        # Mock S3 responses
        mock_s3_client = Mock()
        mock_get_folders.return_value = ["app_data/consultations/test/inputs/question_part_1/"]

        # Mock question file
        question_data = b'{"question_text": ""}'

        # Mock themes file
        themes_data = (
            b'[{"theme_key": "A", "theme_name": "Theme A", "theme_description": "Description A"}]'
        )

        def get_incomplete_object_side_effect(Bucket, Key):
            if "question.json" in Key:
                return {"Body": Mock(read=Mock(return_value=question_data))}
            elif "themes.json" in Key:
                return {"Body": Mock(read=Mock(return_value=themes_data))}
            else:
                return None

        mock_s3_client.get_object.side_effect = get_incomplete_object_side_effect
        mock_boto3.client.return_value = mock_s3_client

        consultation = Consultation.objects.create(title="Test Consultation")
        consultation_code = "test"

        with pytest.raises(ValueError) as exc_info:
            import_questions(
                consultation,
                consultation_code,
                "2024-01-01",
            )

        assert "Question text is required" in str(exc_info.value)


@pytest.mark.django_db
class TestResponsesImport:
    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_import_responses(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        # Mock S3 responses
        mock_s3_client = Mock()
        mock_s3_client.get_object.side_effect = get_object_side_effect
        mock_boto3.client.return_value = mock_s3_client

        consultation = Consultation.objects.create(title="Test Consultation")
        question = Question.objects.create(consultation=consultation, number=1)
        question_folder = "app_data/consultations/test/outputs/2024-01-01/question_part_1/"
        Respondent.objects.create(consultation=consultation, themefinder_id=1)
        Respondent.objects.create(consultation=consultation, themefinder_id=2)

        # Run the import
        responses_file_key = f"{question_folder}responses.jsonl"
        import_responses(question, responses_file_key)

        # Verify results
        responses = Response.objects.filter(question=question)
        assert responses.count() == 2


@pytest.mark.django_db
class TestMappingImport:
    @patch("consultation_analyser.support_console.ingest.boto3")
    @patch("consultation_analyser.support_console.ingest.settings")
    def test_import_mapping(self, mock_settings, mock_boto3):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"

        # Mock S3 responses
        mock_s3_client = Mock()
        mock_s3_client.get_object.side_effect = get_object_side_effect
        mock_boto3.client.return_value = mock_s3_client
        output_folder = "app_data/consultations/test/outputs/mapping/2024-01-01/"

        consultation = Consultation.objects.create(title="Test Consultation")
        question = Question.objects.create(consultation=consultation, number=1)
        Theme.objects.create(question=question, name="name", description="", key="A")
        respondent_1 = Respondent.objects.create(consultation=consultation, themefinder_id=1)
        respondent_2 = Respondent.objects.create(consultation=consultation, themefinder_id=2)
        Response.objects.create(respondent=respondent_1, question=question)
        Response.objects.create(respondent=respondent_2, question=question)

        # Run the import
        import_response_annotations(question, output_folder)

        # Verify results
        annotations = ResponseAnnotation.objects.filter(
            response__question__consultation=consultation
        )
        assert annotations.count() == 2
