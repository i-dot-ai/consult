import pytest
from django.urls import reverse

from factories import DemographicQuestionFactory, ResponseFactory

pytestmark = pytest.mark.django_db


def _url(consultation):
    return reverse("consultations-demographics", kwargs={"pk": consultation.id})


def _counts(payload):
    return {(item["name"], item["value"]): item["count"] for item in payload}


def test_demographics_come_from_demographic_question_rows(client, staff_user_token, closed_answers):
    question = closed_answers.demographic_question

    response = client.get(
        _url(question.consultation), headers={"Authorization": f"Bearer {staff_user_token}"}
    )

    assert response.status_code == 200
    assert response.json() == [
        {"id": f"{question.id}:North", "name": question.text, "value": "North", "count": 2},
        {"id": f"{question.id}:South", "name": question.text, "value": "South", "count": 1},
    ]


def test_demographics_recount_for_a_filtered_respondent_set(
    client, staff_user_token, closed_answers
):
    question = closed_answers.demographic_question

    response = client.get(
        _url(question.consultation),
        query_params={
            "question_id": closed_answers.open_question.id,
            "answers": ["Blue"],
        },
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    assert _counts(response.json()) == {(question.text, "North"): 1, (question.text, "South"): 0}


def test_demographic_answers_filter_ands_across_questions(client, staff_user_token, closed_answers):
    consultation = closed_answers.demographic_question.consultation
    second_question = DemographicQuestionFactory(consultation=consultation, number=15)
    for respondent, value in [(closed_answers.multi_select, "Yes"), (closed_answers.single, "No")]:
        ResponseFactory(question=second_question, respondent=respondent, text=value, free_text=None)

    response = client.get(
        _url(consultation),
        query_params={
            "question_id": closed_answers.open_question.id,
            "demographic_answers": [
                f"{closed_answers.demographic_question.id}:North",
                f"{closed_answers.demographic_question.id}:South",
                f"{second_question.id}:Yes",
            ],
        },
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    counts = _counts(response.json())
    assert counts[(closed_answers.demographic_question.text, "North")] == 1
    assert counts[(closed_answers.demographic_question.text, "South")] == 0
    assert counts[(second_question.text, "Yes")] == 1
    assert counts[(second_question.text, "No")] == 0


def test_legacy_demographics_param_accepts_answer_ids(client, staff_user_token, closed_answers):
    question = closed_answers.demographic_question

    response = client.get(
        _url(question.consultation),
        query_params={
            "question_id": closed_answers.open_question.id,
            "demographics": f"{question.id}:South",
        },
        headers={"Authorization": f"Bearer {staff_user_token}"},
    )

    assert response.status_code == 200
    assert _counts(response.json()) == {(question.text, "North"): 0, (question.text, "South"): 1}
