from unittest.mock import Mock, patch

import pytest
from backend.consultations.models import (
    Consultation,
    Question,
    Respondent,
    Response,
)
from backend.data_pipeline.sync.consultation_setup import (
    import_consultation_from_s3,
)
from backend.factories import UserFactory


@pytest.mark.django_db
class TestImportConsultationFromS3:
    @patch("backend.data_pipeline.sync.consultation_setup.get_queue")
    @patch("backend.data_pipeline.sync.consultation_setup.boto3")
    @patch("backend.data_pipeline.sync.consultation_setup.s3")
    @patch("backend.data_pipeline.sync.consultation_setup.settings")
    def test_import_consultation_from_s3(self, mock_settings, mock_s3, mock_boto3, mock_get_queue):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_boto3.client.return_value = Mock()
        mock_queue = Mock()
        mock_get_queue.return_value = mock_queue

        # Create test user
        user = UserFactory()

        # Mock respondents data
        mock_respondents = [
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

        # Mock question folders
        mock_question_folders = [
            "app_data/consultations/test-code/inputs/question_part_1/",
            "app_data/consultations/test-code/inputs/question_part_2/",
            "app_data/consultations/test-code/inputs/question_part_3/",
        ]

        # Question 1: Free text only
        mock_question_1 = {
            "question_text": "What are your thoughts on this proposal?",
            "has_free_text": True,
            "multi_choice_options": [],
        }

        # Question 2: Multi choice only
        mock_question_2 = {
            "question_text": "Which option do you prefer?",
            "has_free_text": False,
            "multi_choice_options": ["Option A", "Option B", "Option C"],
        }

        # Question 3: Hybrid (both free text and multi choice)
        mock_question_3 = {
            "question_text": "Do you agree? Please explain.",
            "has_free_text": True,
            "multi_choice_options": ["Yes", "No", "Not sure"],
        }

        # Mock responses for free text questions
        mock_responses_q1 = [
            {"themefinder_id": 1, "text": "I strongly support this proposal"},
            {"themefinder_id": 2, "text": "I have some concerns about implementation"},
            {"themefinder_id": 3, "text": "this is response 3"},
            {"themefinder_id": 4, "text": "this is response 4"},
            {"themefinder_id": 5, "text": "this is response 5"},
            {"themefinder_id": 6, "text": "this is response 6"},
            {"themefinder_id": 7, "text": "this is response 7"},
            {"themefinder_id": 8, "text": "this is response 8"},
            {"themefinder_id": 9, "text": "this is response 9"},
            {"themefinder_id": 10, "text": "this is response 10"},
        ]

        mock_responses_q3 = [
            {"themefinder_id": 1, "text": "Yes, I agree because it helps everyone"},
            {"themefinder_id": 3, "text": "Not sure, need more information"},
        ]

        # Mock multi choice responses
        mock_multi_choice_q2 = [
            {"themefinder_id": 1, "options": ["Option A"]},
            {"themefinder_id": 2, "options": ["Option B", "Option C"]},
        ]

        mock_multi_choice_q3 = [
            {"themefinder_id": 1, "options": ["Yes"]},
            {"themefinder_id": 3, "options": ["Not sure"]},
        ]

        def mock_read_jsonl(bucket_name, key, s3_client=None, raise_if_missing=True):
            if "respondents.jsonl" in key:
                return mock_respondents
            elif "question_part_1/responses.jsonl" in key:
                return mock_responses_q1
            elif "question_part_2/responses.jsonl" in key:
                return []  # No free text responses for multi-choice only
            elif "question_part_3/responses.jsonl" in key:
                return mock_responses_q3
            elif "question_part_1/multi_choice.jsonl" in key:
                return []  # No multi choice for free text only
            elif "question_part_2/multi_choice.jsonl" in key:
                return mock_multi_choice_q2
            elif "question_part_3/multi_choice.jsonl" in key:
                return mock_multi_choice_q3
            return []

        def mock_read_json(bucket_name, key, s3_client=None, raise_if_missing=True):
            if "question_part_1/question.json" in key:
                return mock_question_1
            elif "question_part_2/question.json" in key:
                return mock_question_2
            elif "question_part_3/question.json" in key:
                return mock_question_3
            return None

        mock_s3.read_jsonl.side_effect = mock_read_jsonl
        mock_s3.read_json.side_effect = mock_read_json
        mock_s3.get_question_folders.return_value = mock_question_folders

        # Run the import with embeddings enabled
        consultation_id = import_consultation_from_s3(
            consultation_code="test-code",
            consultation_title="Test Consultation",
            user_id=user.id,
            enqueue_embeddings=True,
            batch_size=2,
        )

        # Verify consultation was created
        consultation = Consultation.objects.get(id=consultation_id)
        assert consultation.code == "test-code"
        assert consultation.title == "Test Consultation"
        assert user in consultation.users.all()

        # verify that the number of responses is much larger than the batch size=2
        assert Respondent.objects.filter(consultation=consultation).count() == 10

        # Verify respondents were created with correct themefinder_ids
        respondent_1 = Respondent.objects.get(consultation=consultation, themefinder_id=1)
        respondent_2 = Respondent.objects.get(consultation=consultation, themefinder_id=2)
        respondent_3 = Respondent.objects.get(consultation=consultation, themefinder_id=3)

        # Verify questions were created with correct types
        question_1 = Question.objects.get(consultation=consultation, number=1)
        assert question_1.text == "What are your thoughts on this proposal?"
        assert question_1.has_free_text is True
        assert question_1.has_multiple_choice is False

        question_2 = Question.objects.get(consultation=consultation, number=2)
        assert question_2.text == "Which option do you prefer?"
        assert question_2.has_free_text is False
        assert question_2.has_multiple_choice is True

        question_3 = Question.objects.get(consultation=consultation, number=3)
        assert question_3.text == "Do you agree? Please explain."
        assert question_3.has_free_text is True
        assert question_3.has_multiple_choice is True

        # Verify responses for free text question
        q1_response_1a = Response.objects.get(question=question_1, respondent=respondent_1)
        assert q1_response_1a.free_text == "I strongly support this proposal"

        q1_response_2 = Response.objects.get(question=question_1, respondent=respondent_2)
        assert q1_response_2.free_text == "I have some concerns about implementation"

        # Verify responses for multiple choice question
        q2_response_1 = Response.objects.get(question=question_2, respondent=respondent_1)
        assert [opt.text for opt in q2_response_1.chosen_options.all()] == ["Option A"]

        q2_response_2 = Response.objects.get(question=question_2, respondent=respondent_2)
        assert {opt.text for opt in q2_response_2.chosen_options.all()} == {"Option B", "Option C"}

        # Verify responses for hybrid question
        q3_response_1 = Response.objects.get(question=question_3, respondent=respondent_1)
        assert q3_response_1.free_text == "Yes, I agree because it helps everyone"
        assert [opt.text for opt in q3_response_1.chosen_options.all()] == ["Yes"]

        q3_response_2 = Response.objects.get(question=question_3, respondent=respondent_3)
        assert q3_response_2.free_text == "Not sure, need more information"
        assert [opt.text for opt in q3_response_2.chosen_options.all()] == ["Not sure"]

        # Verify embedding jobs were enqueued for free text questions only
        assert mock_queue.enqueue.call_count == 2
