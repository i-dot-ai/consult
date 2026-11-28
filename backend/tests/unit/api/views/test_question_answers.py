import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def _detail_url(question):
    return reverse(
        "question-detail",
        kwargs={"consultation_pk": question.consultation.id, "pk": question.id},
    )


def test_hybrid_question_lists_answers_from_the_closed_sibling(
    client, staff_user_token, closed_answers
):
    response = client.get(
        _detail_url(closed_answers.open_question),
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["multiple_choice_answer"] == [
        {"id": "Red", "text": "Red", "response_count": 2},
        {"id": "Blue", "text": "Blue", "response_count": 1},
    ]


def test_filtered_question_recounts_answers_for_the_filtered_respondents(
    client, staff_user_token, closed_answers
):
    response = client.get(
        _detail_url(closed_answers.open_question),
        query_params={"answers": ["Blue"]},
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["multiple_choice_answer"] == [
        {"id": "Blue", "text": "Blue", "response_count": 1},
        {"id": "Red", "text": "Red", "response_count": 1},
    ]
    assert data["multi_choice_response_count"] == 1
    assert data["total_response_count"] == 1


def test_question_list_carries_answer_counts(client, staff_user_token, closed_answers):
    response = client.get(
        reverse(
            "question-list",
            kwargs={"consultation_pk": closed_answers.closed_question.consultation.id},
        ),
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    by_number = {item["number"]: item for item in response.json()["results"]}
    assert by_number[11]["multiple_choice_answer"] == [
        {"id": "Red", "text": "Red", "response_count": 2},
        {"id": "Blue", "text": "Blue", "response_count": 1},
    ]
    assert by_number[12]["multiple_choice_answer"] == by_number[11]["multiple_choice_answer"]
    assert by_number[14]["multiple_choice_answer"] == []
