import base64
import json

import pytest
from django.urls import reverse

from consultations.api_v2.demographic_tokens import encode_demographic_token

pytestmark = pytest.mark.django_db


def _list_url(question):
    return reverse(
        "question-response-v2-list",
        kwargs={"consultation_pk": question.consultation.id, "question_pk": question.id},
    )


def _answers_by_identifier(payload):
    return {
        item["identifier"]: item["multiple_choice_answer"] for item in payload["all_respondents"]
    }


def test_v2_responses_carry_the_respondents_selected_answers(
    client, non_staff_user_token, closed_answers
):
    response = client.get(
        _list_url(closed_answers.open_question),
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert _answers_by_identifier(response.json()) == {
        str(closed_answers.multi_select.themefinder_id): ["Blue", "Red"],
        str(closed_answers.single.themefinder_id): ["Red"],
        str(closed_answers.silent.themefinder_id): [],
    }


def test_v2_answers_filter_keeps_respondents_who_selected_any_value(
    client, non_staff_user_token, closed_answers
):
    response = client.get(
        _list_url(closed_answers.open_question),
        query_params={"answers": ["Blue", "Green"]},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert set(_answers_by_identifier(response.json())) == {
        str(closed_answers.multi_select.themefinder_id)
    }


def test_v2_closed_question_responses_carry_their_own_answer(
    client, non_staff_user_token, closed_answers
):
    response = client.get(
        _list_url(closed_answers.closed_question),
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    answers = [
        sorted(item["multiple_choice_answer"]) for item in response.json()["all_respondents"]
    ]
    assert sorted(answers) == [["Blue", "Red"], ["Blue", "Red"], ["Red"]]


def test_v2_demographic_question_responses_carry_their_own_answer(
    client, non_staff_user_token, closed_answers
):
    response = client.get(
        _list_url(closed_answers.demographic_question),
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    answers = [item["multiple_choice_answer"] for item in response.json()["all_respondents"]]
    assert sorted(answers) == [["North"], ["North"], ["South"]]


def test_v2_demographic_answers_filter_takes_repeated_tokens(
    client, non_staff_user_token, closed_answers
):
    south = encode_demographic_token(closed_answers.demographic_question.id, "South")

    response = client.get(
        _list_url(closed_answers.open_question),
        query_params={"demographic_answers": [south]},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert set(_answers_by_identifier(response.json())) == {
        str(closed_answers.single.themefinder_id)
    }


def test_v2_demographic_answers_filter_ignores_a_token_without_a_question_id(
    client, non_staff_user_token, closed_answers
):
    payload = json.dumps({"q": "not-a-question", "v": "South"}).encode()
    token = base64.urlsafe_b64encode(payload).decode().rstrip("=")

    response = client.get(
        _list_url(closed_answers.open_question),
        query_params={"demographic_answers": [token]},
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert len(response.json()["all_respondents"]) == 3
