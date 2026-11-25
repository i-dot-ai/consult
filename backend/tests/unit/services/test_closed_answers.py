import pytest

from consultations.services.closed_answers import (
    count_answering_respondents,
    count_option_responses,
    list_selected_texts,
)
from factories import ResponseFactory

pytestmark = pytest.mark.django_db


def test_option_counts_come_from_the_closed_question_rows(closed_answers):
    assert count_option_responses(closed_answers.closed_question) == [
        {"text": "Red", "response_count": 2},
        {"text": "Blue", "response_count": 1},
    ]


def test_option_counts_for_a_hybrid_read_the_closed_sibling(closed_answers):
    assert count_option_responses(closed_answers.open_question) == count_option_responses(
        closed_answers.closed_question
    )


def test_option_counts_for_a_demographic_question_read_its_own_rows(closed_answers):
    assert count_option_responses(closed_answers.demographic_question) == [
        {"text": "North", "response_count": 2},
        {"text": "South", "response_count": 1},
    ]


def test_option_counts_can_be_limited_to_respondents(closed_answers):
    assert count_option_responses(
        closed_answers.open_question, respondent_ids=[closed_answers.single.id]
    ) == [{"text": "Red", "response_count": 1}]


def test_option_counts_ignore_blank_rows(closed_answers):
    ResponseFactory(
        question=closed_answers.closed_question,
        respondent=closed_answers.silent,
        text="",
        free_text=None,
    )
    assert count_option_responses(closed_answers.closed_question) == [
        {"text": "Red", "response_count": 2},
        {"text": "Blue", "response_count": 1},
    ]


def test_option_counts_are_empty_without_an_answers_question(closed_answers):
    assert count_option_responses(closed_answers.legacy_question) == []


def test_respondent_count_counts_each_respondent_once(closed_answers):
    assert count_answering_respondents(closed_answers.open_question) == 2


def test_respondent_count_can_be_limited_to_respondents(closed_answers):
    assert (
        count_answering_respondents(
            closed_answers.closed_question,
            respondent_ids=[closed_answers.multi_select.id, closed_answers.silent.id],
        )
        == 1
    )


def test_selected_texts_are_grouped_by_respondent(closed_answers):
    respondent_ids = [
        closed_answers.multi_select.id,
        closed_answers.single.id,
        closed_answers.silent.id,
    ]
    assert list_selected_texts(closed_answers.open_question, respondent_ids) == {
        closed_answers.multi_select.id: ["Blue", "Red"],
        closed_answers.single.id: ["Red"],
    }


def test_selected_texts_are_empty_without_an_answers_question(closed_answers):
    assert (
        list_selected_texts(closed_answers.legacy_question, [closed_answers.multi_select.id]) == {}
    )
