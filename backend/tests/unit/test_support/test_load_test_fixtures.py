import pytest

from consultations.models import Consultation, Question, Response
from consultations.test_support.load_test_fixtures import create_data_from_fixtures

pytestmark = pytest.mark.django_db


def _fixtures():
    return {
        "consultations": [
            {
                "title": "Chocolate",
                "stage": Consultation.Stage.ANALYSIS,
                "questions": [
                    {
                        "text": "Why do you agree or disagree?",
                        "number": 1,
                        "type": "open",
                        "closed_question": {"text": "Do you agree?", "number": 101},
                        "responses": [
                            {"free_text": "Because labels help", "chosen_options": ["Yes"]},
                            {"free_text": "", "chosen_options": ["No", "Don't know"]},
                            {"free_text": "No strong view"},
                        ],
                    },
                    {
                        "text": "Which factors matter?",
                        "number": 2,
                        "type": "closed",
                        "responses": [
                            {"chosen_options": ["Price", "Taste"]},
                            {"chosen_options": []},
                            {"chosen_options": ["Taste"]},
                        ],
                    },
                    {
                        "text": "Anything else?",
                        "number": 3,
                        "type": "open",
                        "responses": [{"free_text": "No"}],
                    },
                ],
            }
        ]
    }


def _rows(question):
    return sorted(
        Response.objects.filter(question=question).values_list("respondent__themefinder_id", "text")
    )


def test_fixture_questions_are_typed_and_hybrids_get_a_closed_sibling():
    created = create_data_from_fixtures(_fixtures())

    questions = {
        q.number: q
        for q in Question.objects.filter(consultation_id__in=created["consultation_ids"])
    }
    assert {number: question.type for number, question in questions.items()} == {
        1: "open",
        2: "closed",
        3: "open",
        101: "closed",
    }
    assert questions[1].closed_question == questions[101]
    assert questions[101].text == "Do you agree?"
    assert created["question_ids"] == [questions[1].id, questions[2].id, questions[3].id]


def test_chosen_options_become_rows_on_the_closed_question():
    created = create_data_from_fixtures(_fixtures())
    questions = {
        q.number: q
        for q in Question.objects.filter(consultation_id__in=created["consultation_ids"])
    }

    assert _rows(questions[101]) == [(1, "Yes"), (2, "Don't know"), (2, "No")]
    assert _rows(questions[2]) == [(1, "Price"), (1, "Taste"), (3, "Taste")]
    assert _rows(questions[1]) == [(1, "Because labels help"), (2, None), (3, "No strong view")]
    assert Response.objects.filter(question=questions[101], free_text__isnull=False).count() == 0


def test_fixture_counts_follow_the_rows():
    created = create_data_from_fixtures(_fixtures())
    questions = {
        q.number: q
        for q in Question.objects.filter(consultation_id__in=created["consultation_ids"])
    }

    assert questions[1].multi_choice_response_count == 2
    assert questions[2].total_response_count == 2
    assert questions[2].multi_choice_response_count == 2
    assert questions[101].total_response_count == 2
