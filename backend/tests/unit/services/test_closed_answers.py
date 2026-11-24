import pytest

from consultations.models import Response
from consultations.services.closed_answers import (
    attach_option_counts,
    count_answering_respondents,
    count_option_responses,
    filter_responses_by_answers,
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
    """Every answer stays listed so a filtered chart keeps its bars; only the counts move."""
    assert count_option_responses(
        closed_answers.open_question, respondent_ids=[closed_answers.single.id]
    ) == [{"text": "Red", "response_count": 1}, {"text": "Blue", "response_count": 0}]


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


def test_attach_option_counts_sets_counts_for_every_gated_question(closed_answers):
    questions = [
        closed_answers.closed_question,
        closed_answers.open_question,
        closed_answers.legacy_question,
    ]
    attach_option_counts(questions)

    expected = [
        {"text": "Red", "response_count": 2},
        {"text": "Blue", "response_count": 1},
    ]
    assert closed_answers.closed_question.prefetched_option_counts == expected
    assert closed_answers.open_question.prefetched_option_counts == expected
    assert not hasattr(closed_answers.legacy_question, "prefetched_option_counts")


def test_filter_responses_by_answers_matches_through_the_closed_sibling(closed_answers):
    responses = Response.objects.filter(question=closed_answers.open_question)
    kept = filter_responses_by_answers(responses, ["Blue"])
    assert list(kept.values_list("respondent_id", flat=True)) == [closed_answers.multi_select.id]


def test_filter_responses_by_answers_matches_a_closed_questions_own_rows(closed_answers):
    responses = Response.objects.filter(question=closed_answers.closed_question)
    kept = filter_responses_by_answers(responses, ["Blue"])
    assert set(kept.values_list("respondent_id", flat=True)) == {closed_answers.multi_select.id}
