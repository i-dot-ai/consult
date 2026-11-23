import pytest
from django.urls import reverse

from factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseAnnotationFactory,
    ResponseFactory,
)


def _show_next_url(consultation, question):
    return reverse(
        "question-v2-show-next",
        kwargs={"consultation_pk": consultation.id, "pk": question.id},
    )


def _get(client, url, token):
    return client.get(url, headers={"Authorization": f"Bearer {token}"})


@pytest.mark.django_db
def test_v2_show_next_returns_unreviewed_open_response(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    answer = ResponseFactory(question=question, respondent=respondent, text="an answer")

    response = _get(
        client, _show_next_url(consultation, question), non_staff_user_token
    )

    assert response.status_code == 200
    body = response.json()
    assert body["next_response"]["id"] == str(answer.id)
    assert body["next_response"]["question_id"] == str(question.id)
    assert body["type"] == "open"


@pytest.mark.django_db
def test_v2_show_next_non_open_question_has_no_next(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, type="closed")
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(question=question, respondent=respondent, text="Yes")

    response = _get(
        client, _show_next_url(consultation, question), non_staff_user_token
    )

    assert response.status_code == 200
    body = response.json()
    assert body["next_response"] is None
    assert body["type"] == "closed"
    assert body["message"] == "This question does not have free text responses."


@pytest.mark.django_db
def test_v2_show_next_all_reviewed(client, consultation, non_staff_user_token):
    question = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    reviewed = ResponseFactory(question=question, respondent=respondent, text="reviewed")
    ResponseAnnotationFactory(response=reviewed, human_reviewed=True)

    response = _get(
        client, _show_next_url(consultation, question), non_staff_user_token
    )

    assert response.status_code == 200
    body = response.json()
    assert body["next_response"] is None
    assert body["message"] == "No more responses to review."


@pytest.mark.django_db
def test_v2_show_next_skips_blank_responses(client, consultation, non_staff_user_token):
    question = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(question=question, respondent=respondent, text=None)
    ResponseFactory(question=question, respondent=respondent, text="")

    response = _get(
        client, _show_next_url(consultation, question), non_staff_user_token
    )

    assert response.status_code == 200
    assert response.json()["next_response"] is None


@pytest.mark.django_db
def test_v2_question_list_filters_by_respondent(client, consultation, non_staff_user_token):
    question_answered = QuestionFactory(consultation=consultation, type="open", number=1)
    question_unanswered = QuestionFactory(consultation=consultation, type="open", number=2)
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(question=question_answered, respondent=respondent, text="answer")
    ResponseFactory(
        question=question_unanswered,
        respondent=RespondentFactory(consultation=consultation),
        text="someone else",
    )

    response = _get(
        client,
        f"{reverse('question-v2-list', kwargs={'consultation_pk': consultation.id})}"
        f"?respondent_id={respondent.id}",
        non_staff_user_token,
    )

    assert response.status_code == 200
    assert [q["id"] for q in response.json()] == [str(question_answered.id)]


@pytest.mark.django_db
def test_v2_question_list_rejects_invalid_respondent_filter(
    client, consultation, non_staff_user_token
):
    response = _get(
        client,
        f"{reverse('question-v2-list', kwargs={'consultation_pk': consultation.id})}"
        "?respondent_id=not-a-uuid",
        non_staff_user_token,
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_v2_show_next_forbidden_for_unassigned_user(client, non_staff_user_token):
    other_consultation = ConsultationFactory()
    question = QuestionFactory(consultation=other_consultation, type="open")

    response = _get(
        client, _show_next_url(other_consultation, question), non_staff_user_token
    )

    assert response.status_code == 403
