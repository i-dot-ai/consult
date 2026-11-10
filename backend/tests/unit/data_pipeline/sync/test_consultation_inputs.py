import json
from unittest.mock import MagicMock, patch

import pytest

from consultations.models import Consultation, MultiChoiceAnswer, Response
from data_pipeline.sync.consultation_inputs import (
    assign_consultation_code,
    export_consultation_inputs_to_s3,
    sync_has_free_text_with_type,
)
from factories import (
    ConsultationFactory,
    MultiChoiceAnswerFactory,
    QuestionFactory,
    RespondentFactory,
)


def put_object_calls(mock_s3_client):
    return mock_s3_client.put_object.call_args_list


def question_json_bodies(mock_s3_client):
    return [
        json.loads(call.kwargs["Body"])
        for call in put_object_calls(mock_s3_client)
        if call.kwargs["Key"].endswith("question.json")
    ]


def responses_jsonl_rows(mock_s3_client):
    rows = []
    for call in mock_s3_client.upload_fileobj.call_args_list:
        assert call.args[1] == "test-bucket"  # Bucket is positional: (Fileobj, Bucket, Key)
        lines = call.args[0].read().decode("utf-8").splitlines()
        rows.append((call.args[2], [json.loads(line) for line in lines]))
    return rows


@pytest.mark.django_db
class TestAssignConsultationCode:
    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    def test_generates_and_persists_a_unique_slug_code(self, mock_s3_client):
        consultation = ConsultationFactory(title="My Fancy Consultation!", code="")

        code = assign_consultation_code(consultation)

        # The in-memory instance is not mutated; callers thread the returned code.
        assert consultation.code == ""
        consultation.refresh_from_db()
        assert code == consultation.code
        assert code.startswith("my-fancy-consultation-")
        suffix = code.rsplit("-", 1)[-1]
        assert len(suffix) == 8
        assert int(suffix, 16)  # suffix is hex
        assert not Consultation.objects.exclude(pk=consultation.pk).filter(code=code).exists()
        mock_s3_client.assert_not_called()

    def test_keeps_an_existing_code_untouched(self):
        consultation = ConsultationFactory(title="Existing", code="already-assigned")

        code = assign_consultation_code(consultation)

        assert code == "already-assigned"
        consultation.refresh_from_db()
        assert consultation.code == "already-assigned"

    def test_does_not_overwrite_a_concurrently_assigned_code(self):
        consultation = ConsultationFactory(title="Race Consultation", code="")
        stale_instance = Consultation.objects.get(pk=consultation.pk)
        # Another kickoff assigned a code after our in-memory instance was
        # loaded; its row update must win over the stale blank copy.
        Consultation.objects.filter(pk=consultation.pk).update(code="assigned-by-other")
        stale_instance.code = ""

        code = assign_consultation_code(stale_instance)

        assert code == "assigned-by-other"
        consultation.refresh_from_db()
        assert consultation.code == "assigned-by-other"


@pytest.mark.django_db
class TestSyncHasFreeTextWithType:
    def test_derives_the_flag_from_question_type(self):
        consultation = ConsultationFactory(code="test-code")
        open_question = QuestionFactory(
            consultation=consultation, number=1, type="open", has_free_text=False
        )
        closed_question = QuestionFactory(
            consultation=consultation, number=2, type="closed", has_free_text=True
        )
        demographic_question = QuestionFactory(
            consultation=consultation, number=3, type="demographic", has_free_text=True
        )
        untyped_question = QuestionFactory(consultation=consultation, number=4)

        synced = sync_has_free_text_with_type(consultation)

        assert synced == 3
        open_question.refresh_from_db()
        closed_question.refresh_from_db()
        demographic_question.refresh_from_db()
        untyped_question.refresh_from_db()
        assert open_question.has_free_text is True
        assert closed_question.has_free_text is False
        assert demographic_question.has_free_text is False
        assert untyped_question.has_free_text is True  # kept V1-style default

    def test_questions_without_a_type_keep_their_stored_flag(self):
        """V1-imported questions have no type; the V1 pipeline set the flag."""
        consultation = ConsultationFactory(code="test-code")
        flagged = QuestionFactory(consultation=consultation, number=1, has_free_text=True)
        unflagged = QuestionFactory(consultation=consultation, number=2, has_free_text=False)

        synced = sync_has_free_text_with_type(consultation)

        assert synced == 0
        flagged.refresh_from_db()
        unflagged.refresh_from_db()
        assert flagged.has_free_text is True
        assert unflagged.has_free_text is False

    def test_only_touches_the_target_consultation(self):
        consultation = ConsultationFactory(code="test-code")
        other = ConsultationFactory(code="other-code")
        QuestionFactory(consultation=consultation, number=1, type="closed", has_free_text=True)
        other_open_question = QuestionFactory(
            consultation=other, number=1, type="open", has_free_text=False
        )

        sync_has_free_text_with_type(consultation)

        other_open_question.refresh_from_db()
        assert other_open_question.has_free_text is False


@pytest.mark.django_db
class TestExportConsultationInputsToS3:
    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    @patch("data_pipeline.sync.consultation_inputs.settings")
    def test_writes_question_json_and_responses_jsonl_for_an_open_question(
        self, mock_settings, mock_get_s3_client
    ):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        consultation = ConsultationFactory(code="test-code")
        question = QuestionFactory(
            consultation=consultation, number=1, type="open", has_free_text=True
        )
        respondent_1 = RespondentFactory(consultation=consultation, themefinder_id=1)
        respondent_2 = RespondentFactory(consultation=consultation, themefinder_id=2)
        respondent_3 = RespondentFactory(consultation=consultation, themefinder_id=3)
        Response.objects.create(question=question, respondent=respondent_1, text="   ")
        Response.objects.create(question=question, respondent=respondent_2, text="Loved it")
        Response.objects.create(question=question, respondent=respondent_3, text="Needs work")

        parts = export_consultation_inputs_to_s3(consultation, "test-code")

        assert parts == 1
        assert (
            mock_s3_client.put_object.call_args.kwargs["Key"]
            == "app_data/consultations/test-code/inputs/question_part_1/question.json"
        )
        assert json.loads(mock_s3_client.put_object.call_args.kwargs["Body"]) == {
            "question_number": 1,
            "question_text": question.text,
            "has_free_text": True,
        }
        [(key, rows)] = responses_jsonl_rows(mock_s3_client)
        assert key == "app_data/consultations/test-code/inputs/question_part_1/responses.jsonl"
        assert rows == [
            {"themefinder_id": 2, "text": "Loved it"},
            {"themefinder_id": 3, "text": "Needs work"},
        ]

    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    @patch("data_pipeline.sync.consultation_inputs.settings")
    def test_closed_question_gets_question_json_with_options_but_no_responses(
        self, mock_settings, mock_get_s3_client
    ):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        consultation = ConsultationFactory(code="test-code")
        question = QuestionFactory(
            consultation=consultation,
            number=2,
            type="closed",
            has_free_text=False,
            has_multiple_choice=True,
        )
        MultiChoiceAnswerFactory(question=question, text="red")
        MultiChoiceAnswerFactory(question=question, text="blue")
        respondent = RespondentFactory(consultation=consultation, themefinder_id=1)
        response = Response.objects.create(question=question, respondent=respondent, text="red")
        response.chosen_options.add(MultiChoiceAnswer.objects.get(text="red"))

        export_consultation_inputs_to_s3(consultation, "test-code")

        [body] = question_json_bodies(mock_s3_client)
        assert body == {
            "question_number": 2,
            "question_text": question.text,
            "has_free_text": False,
            "multi_choice_options": ["blue", "red"],
        }
        assert mock_s3_client.upload_fileobj.call_count == 0

    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    @patch("data_pipeline.sync.consultation_inputs.settings")
    def test_hybrid_respondent_with_choices_but_no_text_gets_not_provided(
        self, mock_settings, mock_get_s3_client
    ):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        consultation = ConsultationFactory(code="test-code")
        question = QuestionFactory(
            consultation=consultation,
            number=7,
            type="open",
            has_free_text=True,
            has_multiple_choice=True,
        )
        option = MultiChoiceAnswerFactory(question=question, text="Yes")
        respondent_with_text = RespondentFactory(consultation=consultation, themefinder_id=1)
        respondent_choice_only = RespondentFactory(consultation=consultation, themefinder_id=2)
        Response.objects.create(
            question=question, respondent=respondent_with_text, text="Behind the printer"
        )
        choice_only = Response.objects.create(
            question=question, respondent=respondent_choice_only, text=None
        )
        choice_only.chosen_options.add(option)

        export_consultation_inputs_to_s3(consultation, "test-code")

        [(key, rows)] = responses_jsonl_rows(mock_s3_client)
        assert key.endswith("question_part_7/responses.jsonl")
        assert rows == [
            {"themefinder_id": 1, "text": "Behind the printer"},
            {"themefinder_id": 2, "text": "Not Provided"},
        ]

    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    @patch("data_pipeline.sync.consultation_inputs.settings")
    def test_hybrid_choices_on_a_linked_closed_question_fill_not_provided(
        self, mock_settings, mock_get_s3_client
    ):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        consultation = ConsultationFactory(code="test-code")
        closed_part = QuestionFactory(
            consultation=consultation,
            number=8,
            type="closed",
            has_free_text=False,
            has_multiple_choice=True,
        )
        open_part = QuestionFactory(
            consultation=consultation,
            number=7,
            type="open",
            has_free_text=True,
            closed_question=closed_part,
        )
        respondent = RespondentFactory(consultation=consultation, themefinder_id=1)
        Response.objects.create(question=closed_part, respondent=respondent, text="Yes")
        Response.objects.create(question=open_part, respondent=respondent, text=None)
        respondent_without_answer = RespondentFactory(consultation=consultation, themefinder_id=2)
        Response.objects.create(question=open_part, respondent=respondent_without_answer, text=None)

        export_consultation_inputs_to_s3(consultation, "test-code")

        [(key, rows)] = responses_jsonl_rows(mock_s3_client)
        assert key.endswith("question_part_7/responses.jsonl")
        assert rows == [{"themefinder_id": 1, "text": "Not Provided"}]

    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    @patch("data_pipeline.sync.consultation_inputs.settings")
    def test_open_responses_without_text_or_choices_are_dropped(
        self, mock_settings, mock_get_s3_client
    ):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        consultation = ConsultationFactory(code="test-code")
        question = QuestionFactory(
            consultation=consultation, number=1, type="open", has_free_text=True
        )
        respondent = RespondentFactory(consultation=consultation, themefinder_id=1)
        Response.objects.create(question=question, respondent=respondent, text="   ")

        parts = export_consultation_inputs_to_s3(consultation, "test-code")

        assert parts == 1  # the folder is still written
        [body] = question_json_bodies(mock_s3_client)
        assert body["has_free_text"] is True
        assert mock_s3_client.upload_fileobj.call_count == 0  # but responses.jsonl is not

    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    @patch("data_pipeline.sync.consultation_inputs.settings")
    def test_question_without_any_responses_is_omitted(self, mock_settings, mock_get_s3_client):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        consultation = ConsultationFactory(code="test-code")
        QuestionFactory(consultation=consultation, number=1, type="open")
        QuestionFactory(consultation=consultation, number=2, type="closed")

        parts = export_consultation_inputs_to_s3(consultation, "test-code")

        assert parts == 0
        assert mock_s3_client.put_object.call_count == 0
        assert mock_s3_client.upload_fileobj.call_count == 0

    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    @patch("data_pipeline.sync.consultation_inputs.settings")
    def test_not_provided_is_not_a_multi_choice_option(self, mock_settings, mock_get_s3_client):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        consultation = ConsultationFactory(code="test-code")
        question = QuestionFactory(
            consultation=consultation,
            number=1,
            type="open",
            has_free_text=True,
            has_multiple_choice=True,
        )
        MultiChoiceAnswerFactory(question=question, text="Not Provided")
        MultiChoiceAnswerFactory(question=question, text="Yes")
        respondent = RespondentFactory(consultation=consultation, themefinder_id=1)
        Response.objects.create(question=question, respondent=respondent, text=None)

        export_consultation_inputs_to_s3(consultation, "test-code")

        [body] = question_json_bodies(mock_s3_client)
        assert body["multi_choice_options"] == ["Yes"]

    def test_requires_a_consultation_code(self):
        consultation = ConsultationFactory(code="")

        with pytest.raises(RuntimeError, match="Empty consultation code"):
            export_consultation_inputs_to_s3(consultation, "")

    @patch("data_pipeline.sync.consultation_inputs.get_s3_client")
    @patch("data_pipeline.sync.consultation_inputs.settings")
    def test_counts_all_exported_question_parts(self, mock_settings, mock_get_s3_client):
        mock_settings.AWS_BUCKET_NAME = "test-bucket"
        mock_s3_client = MagicMock()
        mock_get_s3_client.return_value = mock_s3_client
        consultation = ConsultationFactory(code="test-code")
        for number in (1, 2, 3):
            respondent = RespondentFactory(consultation=consultation, themefinder_id=number)
            question = QuestionFactory(
                consultation=consultation, number=number, type="open", has_free_text=True
            )
            Response.objects.create(
                question=question, respondent=respondent, text=f"answer {number}"
            )

        parts = export_consultation_inputs_to_s3(consultation, "test-code")

        assert parts == 3
        assert mock_s3_client.put_object.call_count == 3
        assert mock_s3_client.upload_fileobj.call_count == 3
        exported_keys = {call.args[2] for call in mock_s3_client.upload_fileobj.call_args_list}
        assert exported_keys == {
            f"app_data/consultations/test-code/inputs/question_part_{number}/responses.jsonl"
            for number in (1, 2, 3)
        }
