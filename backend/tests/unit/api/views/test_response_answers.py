import pytest
from django.urls import reverse

from factories import ResponseFactory

pytestmark = pytest.mark.django_db


def _list_url(question):
    return reverse(
        "question-response-list",
        kwargs={"consultation_pk": question.consultation.id, "question_pk": question.id},
    )


def _answers_by_identifier(payload):
    return {
        item["identifier"]: item["multiple_choice_answer"] for item in payload["all_respondents"]
    }


def test_responses_carry_the_respondents_selected_answers(client, staff_user_token, closed_answers):
    response = client.get(
        _list_url(closed_answers.open_question),
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    assert _answers_by_identifier(response.json()) == {
        str(closed_answers.multi_select.themefinder_id): ["Blue", "Red"],
        str(closed_answers.single.themefinder_id): ["Red"],
        str(closed_answers.silent.themefinder_id): [],
    }


def test_answers_filter_keeps_respondents_who_selected_any_value(
    client, staff_user_token, closed_answers
):
    response = client.get(
        _list_url(closed_answers.open_question),
        query_params={"answers": ["Blue"]},
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    assert set(_answers_by_identifier(response.json())) == {
        str(closed_answers.multi_select.themefinder_id)
    }


def test_answers_filter_accepts_values_containing_commas(client, staff_user_token, closed_answers):
    ResponseFactory(
        question=closed_answers.closed_question,
        respondent=closed_answers.silent,
        text="Yes, strongly",
        free_text=None,
    )

    response = client.get(
        _list_url(closed_answers.open_question),
        query_params={"answers": ["Yes, strongly", "Blue"]},
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    assert set(_answers_by_identifier(response.json())) == {
        str(closed_answers.multi_select.themefinder_id),
        str(closed_answers.silent.themefinder_id),
    }


def test_legacy_multiple_choice_param_accepts_answer_texts(
    client, staff_user_token, closed_answers
):
    response = client.get(
        _list_url(closed_answers.open_question),
        query_params={"multiple_choice_answer": "Red"},
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    assert set(_answers_by_identifier(response.json())) == {
        str(closed_answers.multi_select.themefinder_id),
        str(closed_answers.single.themefinder_id),
    }
