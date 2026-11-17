import pytest
from django.urls import reverse

from factories import (
    ConsultationFactory,
    MultiChoiceAnswerFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactory,
    ResponseFactory,
)


def _url(consultation, question, qs=""):
    return (
        reverse("question-v2-detail", kwargs={"consultation_pk": consultation.id, "pk": question.id})
        + qs
    )


def _get(client, url, token):
    return client.get(url, headers={"Authorization": f"Bearer {token}"})


@pytest.mark.django_db
def test_v2_question_retrieve_exposes_dashboard_fields(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, type="open")

    response = _get(client, _url(consultation, question), non_staff_user_token)

    assert response.status_code == 200
    body = response.json()
    for field in (
        "text",
        "type",
        "closed_question",
        "dashboard_role",
        "response_count",
        "total_response_count",
        "free_text_response_count",
        "multi_choice_response_count",
        "multiple_choice_answer",
        "proportion_of_audited_answers",
    ):
        assert field in body
    assert body["text"] == question.text
    assert body["type"] == "open"


@pytest.mark.django_db
def test_v2_question_retrieve_recovers_counts_under_search_filter(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(question=question, respondent=respondent, text="flooding near the river")
    ResponseFactory(question=question, respondent=respondent, text="bus cuts announced")

    response = _get(
        client,
        _url(consultation, question, "?searchValue=flooding&searchMode=keyword"),
        non_staff_user_token,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_response_count"] == 1
    assert body["free_text_response_count"] == 1


@pytest.mark.django_db
def test_v2_question_retrieve_annotates_multiple_choice_counts_under_filters(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(
        consultation=consultation, type="closed", has_free_text=False, has_multiple_choice=True
    )
    yes_answer = MultiChoiceAnswerFactory(question=question, text="Yes")
    MultiChoiceAnswerFactory(question=question, text="No")
    r1, r2 = RespondentFactory(consultation=consultation), RespondentFactory(consultation=consultation)
    ResponseFactory(question=question, respondent=r1, text="Yes", free_text=None).chosen_options.add(
        yes_answer
    )
    ResponseFactory(question=question, respondent=r2, text="No", free_text=None)

    response = _get(
        client,
        _url(consultation, question, "?searchValue=Yes&searchMode=keyword"),
        non_staff_user_token,
    )

    assert response.status_code == 200
    counts = {
        item["text"]: item["response_count"] for item in response.json()["multiple_choice_answer"]
    }
    assert counts == {"Yes": 1, "No": 0}


@pytest.mark.django_db
def test_v2_question_retrieve_proportion_of_audited_answers(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    reviewed = ResponseFactory(question=question, respondent=respondent, text="reviewed answer")
    ResponseFactory(question=question, respondent=respondent, text="unreviewed answer")
    ResponseAnnotationFactory(response=reviewed, human_reviewed=True)

    response = _get(client, _url(consultation, question), non_staff_user_token)

    assert response.status_code == 200
    assert response.json()["proportion_of_audited_answers"] == 0.5


@pytest.mark.django_db
def test_v2_question_retrieve_staff_can_read_any_consultation(
    client, staff_user_token
):
    other_consultation = ConsultationFactory()
    question = QuestionFactory(consultation=other_consultation, type="open")

    response = _get(client, _url(other_consultation, question), staff_user_token)

    assert response.status_code == 200
