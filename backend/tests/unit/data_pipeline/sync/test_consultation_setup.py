import json
from unittest.mock import patch

import pytest
from botocore.exceptions import ClientError
from django.conf import settings
from django.db.models import Count

from consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
)
from data_pipeline.sync.consultation_setup import (
    import_consultation_from_s3,
    load_question_from_s3,
    load_respondents_from_s3,
)
from factories import UserFactory

logger = settings.LOGGER


def _client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "GetObject")


@pytest.mark.django_db
class TestImportConsultationFromS3:
    @patch("data_pipeline.sync.consultation_setup.create_embeddings_for_question.enqueue")
    def test_import_consultation_from_s3(self, mock_enqueue, minio_test_bucket, minio_client):
        """
        Test importing a complete consultation from S3 with multiple question types.

        Creates real S3 objects representing:
        - Respondents with demographics
        - Question 1: Free text only
        - Question 2: Multi choice only
        - Question 3: Hybrid (both free text and multi choice)
        """

        # Track objects we create for cleanup
        created_keys = []

        try:
            # Create test user
            user = UserFactory()

            # Setup: Prepare test data

            # Respondents data
            respondents = [
                {"themefinder_id": 1, "demographic_data": {"age": ["25-34"]}},
                {"themefinder_id": 2, "demographic_data": {"region": ["North"]}},
                {"themefinder_id": 3, "demographic_data": {}},
                {"themefinder_id": 4, "demographic_data": {}},
                {"themefinder_id": 5, "demographic_data": {}},
                {"themefinder_id": 6, "demographic_data": {}},
                {"themefinder_id": 7, "demographic_data": {}},
                {"themefinder_id": 8, "demographic_data": {}},
                {"themefinder_id": 9, "demographic_data": {}},
                {"themefinder_id": 10, "demographic_data": {}},
            ]

            # Question 1: Free text only
            question_1 = {
                "question_text": "What are your thoughts on this proposal?",
                "has_free_text": True,
                "multi_choice_options": [],
            }

            # Question 2: Multi choice only
            question_2 = {
                "question_text": "Which option do you prefer?",
                "has_free_text": False,
                "multi_choice_options": ["Option A", "Option B", "Option C"],
            }

            # Question 3: Hybrid (both free text and multi choice)
            question_3 = {
                "question_text": "Do you agree? Please explain.",
                "has_free_text": True,
                "multi_choice_options": ["Yes", "No", "Not sure"],
            }

            # Responses for free text questions
            responses_q1 = [
                {"themefinder_id": 1, "text": "I strongly support this proposal"},
                {"themefinder_id": 2, "text": "I have some concerns about implementation"},
            ]

            responses_q3 = [
                {"themefinder_id": 1, "text": "Yes, I agree because it helps everyone"},
                {"themefinder_id": 3, "text": "Not sure, need more information"},
            ]

            # Multi choice responses
            multi_choice_q2 = [
                {"themefinder_id": 1, "options": ["Option A"]},
                {"themefinder_id": 2, "options": ["Option B", "Option C"]},
                {"themefinder_id": 3, "options": ["Option C"]},
                {"themefinder_id": 4, "options": ["Option A"]},
                {"themefinder_id": 5, "options": ["Option B"]},
                {"themefinder_id": 6, "options": ["Option C"]},
                {"themefinder_id": 7, "options": ["Option A"]},
                {"themefinder_id": 8, "options": ["Option B"]},
                {"themefinder_id": 9, "options": ["Option C"]},
                {"themefinder_id": 10, "options": ["Option A"]},
            ]

            multi_choice_q3 = [
                {"themefinder_id": 1, "options": ["Yes"]},
                {"themefinder_id": 3, "options": ["Not sure"]},
            ]

            # Setup: Create S3 objects in MinIO

            # Create respondents.jsonl
            key = "app_data/consultations/test-code/inputs/respondents.jsonl"
            body = "\n".join([json.dumps(r) for r in respondents])
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=body.encode())
            created_keys.append(key)

            # Create question 1 files (free text only)
            key = "app_data/consultations/test-code/inputs/question_part_1/question.json"
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=json.dumps(question_1).encode())
            created_keys.append(key)

            key = "app_data/consultations/test-code/inputs/question_part_1/responses.jsonl"
            body = "\n".join([json.dumps(r) for r in responses_q1])
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=body.encode())
            created_keys.append(key)

            key = "app_data/consultations/test-code/inputs/question_part_1/multi_choice.jsonl"
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=b"")  # Empty file
            created_keys.append(key)

            # Create question 2 files (multi choice only)
            key = "app_data/consultations/test-code/inputs/question_part_2/question.json"
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=json.dumps(question_2).encode())
            created_keys.append(key)

            key = "app_data/consultations/test-code/inputs/question_part_2/responses.jsonl"
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=b"")  # Empty file
            created_keys.append(key)

            key = "app_data/consultations/test-code/inputs/question_part_2/multi_choice.jsonl"
            body = "\n".join([json.dumps(r) for r in multi_choice_q2])
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=body.encode())
            created_keys.append(key)

            # Create question 3 files (hybrid)
            key = "app_data/consultations/test-code/inputs/question_part_3/question.json"
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=json.dumps(question_3).encode())
            created_keys.append(key)

            key = "app_data/consultations/test-code/inputs/question_part_3/responses.jsonl"
            body = "\n".join([json.dumps(r) for r in responses_q3])
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=body.encode())
            created_keys.append(key)

            key = "app_data/consultations/test-code/inputs/question_part_3/multi_choice.jsonl"
            body = "\n".join([json.dumps(r) for r in multi_choice_q3])
            minio_client.put_object(Bucket=minio_test_bucket, Key=key, Body=body.encode())
            created_keys.append(key)

            # Execute: Run the import with embeddings enabled
            consultation_id = import_consultation_from_s3(
                consultation_code="test-code",
                consultation_title="Test Consultation",
                user_id=user.id,
                enqueue_embeddings=True,
                batch_size=2,
            )

            # Verify: Check consultation was created correctly
            consultation = Consultation.objects.get(id=consultation_id)
            assert consultation.code == "test-code"
            assert consultation.title == "Test Consultation"
            assert user in consultation.users.all()

            # Verify that the number of responses is much larger than the batch size=2
            assert Respondent.objects.filter(consultation=consultation).count() == 10

            # Verify respondents were created with correct themefinder_ids
            respondent_1 = Respondent.objects.get(consultation=consultation, themefinder_id=1)
            respondent_2 = Respondent.objects.get(consultation=consultation, themefinder_id=2)
            respondent_3 = Respondent.objects.get(consultation=consultation, themefinder_id=3)

            # Verify questions were created with correct types
            question_1_db = Question.objects.get(consultation=consultation, number=1)
            assert question_1_db.text == "What are your thoughts on this proposal?"
            assert question_1_db.has_free_text is True
            assert question_1_db.has_multiple_choice is False

            question_2_db = Question.objects.get(consultation=consultation, number=2)
            assert question_2_db.text == "Which option do you prefer?"
            assert question_2_db.has_free_text is False
            assert question_2_db.has_multiple_choice is True

            question_3_db = Question.objects.get(consultation=consultation, number=3)
            assert question_3_db.text == "Do you agree? Please explain."
            assert question_3_db.has_free_text is True
            assert question_3_db.has_multiple_choice is True

            # Verify responses for free text question
            q1_response_1 = Response.objects.get(question=question_1_db, respondent=respondent_1)
            assert q1_response_1.free_text == "I strongly support this proposal"

            q1_response_2 = Response.objects.get(question=question_1_db, respondent=respondent_2)
            assert q1_response_2.free_text == "I have some concerns about implementation"

            # Verify that q2 has 10 responses
            assert Response.objects.filter(question=question_2_db).count() == 10

            # Verify that all 10 responses to q2 have at least one multi choice answer
            assert (
                Response.objects.filter(question=question_2_db)
                .values("respondent")
                .annotate(count=Count("chosen_options"))
                .filter(count__gt=0)
                .count()
                == 10
            )

            # Verify responses for multiple choice question
            q2_response_1 = Response.objects.get(question=question_2_db, respondent=respondent_1)
            assert [opt.text for opt in q2_response_1.chosen_options.all()] == ["Option A"]

            q2_response_2 = Response.objects.get(question=question_2_db, respondent=respondent_2)
            assert {opt.text for opt in q2_response_2.chosen_options.all()} == {"Option B", "Option C"}

            # Verify responses for hybrid question
            q3_response_1 = Response.objects.get(question=question_3_db, respondent=respondent_1)
            assert q3_response_1.free_text == "Yes, I agree because it helps everyone"
            assert [opt.text for opt in q3_response_1.chosen_options.all()] == ["Yes"]

            q3_response_2 = Response.objects.get(question=question_3_db, respondent=respondent_3)
            assert q3_response_2.free_text == "Not sure, need more information"
            assert [opt.text for opt in q3_response_2.chosen_options.all()] == ["Not sure"]

            # Verify embedding jobs were enqueued for free text questions only
            assert mock_enqueue.call_count == 2

        finally:
            # Cleanup: Delete all objects we created
            for key in created_keys:
                try:
                    minio_client.delete_object(
                        Bucket=minio_test_bucket,
                        Key=key
                    )
                except Exception as e:
                    logger.warning("Failed to cleanup object {key}: {e}", key=key, e=e)


class TestLoadRespondentsFromS3:
    @patch("data_pipeline.sync.consultation_setup.s3.read_jsonl")
    def test_raises_value_error_when_file_missing(self, mock_read_jsonl):
        mock_read_jsonl.side_effect = _client_error("NoSuchKey")

        with pytest.raises(ValueError) as exc_info:
            load_respondents_from_s3(
                consultation_code="test-code",
                bucket_name="test-bucket",
            )

        assert "respondents.jsonl" in str(exc_info.value)
        assert isinstance(exc_info.value.__cause__, ClientError)

    @patch("data_pipeline.sync.consultation_setup.s3.read_jsonl")
    def test_propagates_non_missing_client_error_unchanged(self, mock_read_jsonl):
        mock_read_jsonl.side_effect = _client_error("AccessDenied")

        with pytest.raises(ClientError) as exc_info:
            load_respondents_from_s3(
                consultation_code="test-code",
                bucket_name="test-bucket",
            )

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"


class TestLoadQuestionFromS3:
    @patch("data_pipeline.sync.consultation_setup.s3.read_json")
    def test_raises_value_error_when_file_missing(self, mock_read_json):
        mock_read_json.side_effect = _client_error("NoSuchKey")

        with pytest.raises(ValueError) as exc_info:
            load_question_from_s3(
                consultation_code="test-code",
                question_number=1,
                bucket_name="test-bucket",
            )

        message = str(exc_info.value)
        assert "question_part_1" in message
        assert isinstance(exc_info.value.__cause__, ClientError)

    @patch("data_pipeline.sync.consultation_setup.s3.read_json")
    def test_propagates_non_missing_client_error_unchanged(self, mock_read_json):
        mock_read_json.side_effect = _client_error("AccessDenied")

        with pytest.raises(ClientError) as exc_info:
            load_question_from_s3(
                consultation_code="test-code",
                question_number=1,
                bucket_name="test-bucket",
            )

        assert exc_info.value.response["Error"]["Code"] == "AccessDenied"
