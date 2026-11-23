from unittest.mock import patch

import pytest

from consultations.models import Consultation, Question, Response
from data_pipeline.models import ConsultationDataBatch, QuestionInput, ResponseInput
from data_pipeline.sync.consultation_setup import (
    import_consultation_data,
    load_answers_from_s3,
    load_consultation_data_batch,
)

pytestmark = pytest.mark.django_db


def _batch():
    return ConsultationDataBatch(
        consultation_code="chocolate",
        consultation_title="Chocolate bars",
        respondents=[
            {"themefinder_id": 1, "demographic_data": {"Nation": ["England"], "Age": ["18-35"]}},
            {"themefinder_id": 2, "demographic_data": {"Nation": ["Wales", "England"]}},
            {"themefinder_id": 3},
        ],
        questions=[
            {"question_text": "Do you agree?", "question_number": 1, "type": "closed"},
            {
                "question_text": "Why?",
                "question_number": 2,
                "type": "open",
                "closed_question_number": 1,
            },
            {"question_text": "Which factors matter?", "question_number": 3, "type": "closed"},
        ],
        responses_by_question={
            2: [
                {"themefinder_id": 1, "text": "Clear labels help"},
                {"themefinder_id": 2, "text": "Not Provided"},
                {"themefinder_id": 3, "text": "   "},
            ]
        },
        answers_by_question={
            1: [
                {"themefinder_id": 1, "text": "Yes"},
                {"themefinder_id": 2, "text": "No"},
                {"themefinder_id": 3, "text": "Yes"},
            ],
            3: [
                {"themefinder_id": 1, "text": "Price"},
                {"themefinder_id": 1, "text": "Taste"},
                {"themefinder_id": 2, "text": "Taste"},
            ],
        },
    )


def _rows(question):
    return sorted(
        Response.objects.filter(question=question).values_list("respondent__themefinder_id", "text")
    )


def test_import_creates_questions_and_links_the_hybrid(staff_user):
    consultation_id = import_consultation_data(_batch(), staff_user.id)

    questions = {q.number: q for q in Question.objects.filter(consultation_id=consultation_id)}
    assert {number: question.type for number, question in questions.items()} == {
        1: "closed",
        2: "open",
        3: "closed",
        4: "demographic",
        5: "demographic",
    }
    assert questions[2].closed_question == questions[1]
    assert questions[1].has_free_text is False
    assert questions[1].has_multiple_choice is True
    assert questions[2].has_free_text is True
    assert [questions[4].text, questions[5].text] == ["Nation", "Age"]


def test_import_stores_every_answer_type_as_response_rows(staff_user):
    consultation_id = import_consultation_data(_batch(), staff_user.id)
    questions = {q.number: q for q in Question.objects.filter(consultation_id=consultation_id)}

    assert _rows(questions[1]) == [(1, "Yes"), (2, "No"), (3, "Yes")]
    assert _rows(questions[2]) == [(1, "Clear labels help")]
    assert _rows(questions[3]) == [(1, "Price"), (1, "Taste"), (2, "Taste")]
    assert _rows(questions[4]) == [(1, "England"), (2, "England"), (2, "Wales")]
    assert _rows(questions[5]) == [(1, "18-35")]

    open_response = Response.objects.get(question=questions[2])
    assert open_response.free_text == "Clear labels help"
    assert Response.objects.filter(question=questions[1], free_text__isnull=False).count() == 0


def test_import_refreshes_the_denormalised_counts(staff_user):
    consultation_id = import_consultation_data(_batch(), staff_user.id)
    questions = {q.number: q for q in Question.objects.filter(consultation_id=consultation_id)}

    assert questions[1].total_response_count == 3
    assert questions[1].multi_choice_response_count == 3
    assert questions[2].total_response_count == 3
    assert questions[2].free_text_response_count == 1
    assert questions[2].multi_choice_response_count == 3


def test_import_counts_a_hybrid_whose_closed_sibling_comes_later(staff_user):
    batch = _batch()
    batch.questions = [
        QuestionInput(
            question_text="Why?", question_number=1, type="open", closed_question_number=2
        ),
        QuestionInput(question_text="Do you agree?", question_number=2, type="closed"),
    ]
    batch.responses_by_question = {1: [ResponseInput(themefinder_id=1, text="Clear labels help")]}
    batch.answers_by_question = {
        2: [ResponseInput(themefinder_id=2, text="No"), ResponseInput(themefinder_id=3, text="Yes")]
    }

    consultation_id = import_consultation_data(batch, staff_user.id)
    hybrid = Question.objects.get(consultation_id=consultation_id, number=1)
    assert hybrid.total_response_count == 3
    assert hybrid.multi_choice_response_count == 2


def test_import_is_idempotent(staff_user):
    consultation_id = import_consultation_data(_batch(), staff_user.id)
    assert import_consultation_data(_batch(), staff_user.id) == consultation_id

    assert Consultation.objects.filter(code="chocolate").count() == 1
    assert Question.objects.filter(consultation_id=consultation_id).count() == 5
    assert Response.objects.filter(question__consultation_id=consultation_id).count() == 11


def test_import_skips_rows_for_unknown_respondents(staff_user):
    batch = _batch()
    batch.answers_by_question[1].append(ResponseInput(themefinder_id=99, text="Yes"))

    consultation_id = import_consultation_data(batch, staff_user.id)
    question = Question.objects.get(consultation_id=consultation_id, number=1)
    assert _rows(question) == [(1, "Yes"), (2, "No"), (3, "Yes")]


@patch("data_pipeline.sync.consultation_setup.s3.read_jsonl")
def test_load_answers_reads_the_answers_file(mock_read_jsonl):
    mock_read_jsonl.return_value = [
        {"themefinder_id": 1, "text": "Yes"},
        {"themefinder_id": 2, "text": ""},
        {"themefinder_id": 3, "text": None},
    ]

    answers = load_answers_from_s3("chocolate", 1, "test-bucket")

    assert mock_read_jsonl.call_args.args == (
        "test-bucket",
        "app_data/consultations/chocolate/inputs/question_part_1/answers.jsonl",
    )
    assert [(answer.themefinder_id, answer.text) for answer in answers] == [(1, "Yes")]


@patch("data_pipeline.sync.consultation_setup.s3.read_jsonl")
@patch("data_pipeline.sync.consultation_setup.s3.read_json")
@patch("data_pipeline.sync.consultation_setup.s3.get_question_folders")
def test_load_batch_reads_responses_for_open_and_answers_for_closed(
    mock_get_question_folders, mock_read_json, mock_read_jsonl
):
    prefix = "app_data/consultations/chocolate/inputs"
    mock_get_question_folders.return_value = [
        f"{prefix}/question_part_1/",
        f"{prefix}/question_part_2/",
    ]
    mock_read_json.side_effect = [
        {"question_text": "Agree?", "type": "closed"},
        {"question_text": "Why?", "type": "open", "closed_question_number": 1},
    ]
    files = {
        f"{prefix}/respondents.jsonl": [{"themefinder_id": 1}],
        f"{prefix}/question_part_1/answers.jsonl": [{"themefinder_id": 1, "text": "Yes"}],
        f"{prefix}/question_part_2/responses.jsonl": [{"themefinder_id": 1, "text": "Because"}],
    }
    mock_read_jsonl.side_effect = lambda bucket, key, raise_if_missing=True: files[key]

    batch = load_consultation_data_batch("chocolate", "Chocolate bars", "test-bucket")

    assert batch.questions[1].closed_question_number == 1
    assert [answer.text for answer in batch.answers_by_question[1]] == ["Yes"]
    assert [response.text for response in batch.responses_by_question[2]] == ["Because"]
    assert set(files) == {call.args[1] for call in mock_read_jsonl.call_args_list}


def test_import_takes_demographic_answers_from_the_answers_file_when_declared(staff_user):
    batch = _batch()
    batch.questions.append(
        QuestionInput(question_text="Nation", question_number=4, type="demographic")
    )
    batch.answers_by_question[4] = [
        ResponseInput(themefinder_id=1, text="Scotland"),
        ResponseInput(themefinder_id=3, text="Wales"),
    ]

    consultation_id = import_consultation_data(batch, staff_user.id)

    nation_questions = Question.objects.filter(consultation_id=consultation_id, text="Nation")
    assert nation_questions.count() == 1
    assert _rows(nation_questions.get()) == [(1, "Scotland"), (3, "Wales")]
    assert Question.objects.filter(consultation_id=consultation_id, text="Age").exists()
