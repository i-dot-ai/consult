import pytest
from django.urls import reverse

from factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
)

RESPONSE_DETAIL_FIELDS = {
    "id",
    "identifier",
    "respondent_id",
    "respondent",
    "question_id",
    "text",
    "demographic_data",
    "themes",
    "multiple_choice_answer",
    "evidenceRich",
    "sentiment",
    "human_reviewed",
    "is_flagged",
    "is_edited",
    "is_read",
}


def _list_url(consultation, question=None):
    kwargs = {"consultation_pk": consultation.id}
    if question is not None:
        kwargs["question_pk"] = question.id
    return reverse("question-response-v2-list", kwargs=kwargs)


def _detail_url(consultation, question, response):
    return reverse(
        "question-response-v2-detail",
        kwargs={"consultation_pk": consultation.id, "question_pk": question.id, "pk": response.id},
    )


def _get(client, url, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return client.get(url, headers=headers)


@pytest.mark.django_db
def test_v2_response_list_returns_only_answered_responses(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(question=question, respondent=respondent, text="An answer")
    ResponseFactory(question=question, respondent=respondent, text=None)
    ResponseFactory(question=question, respondent=respondent, text="")

    response = _get(client, _list_url(consultation, question), non_staff_user_token)

    assert response.status_code == 200
    assert response.json()["total_count"] == 1
    assert response.json()["all_respondents"][0]["text"] == "An answer"


@pytest.mark.django_db
def test_v2_response_list_exposes_v2_payload_shape(client, consultation, non_staff_user_token):
    question = QuestionFactory(consultation=consultation, type="open")
    ResponseFactory(
        question=question, respondent=RespondentFactory(consultation=consultation), text="Hello"
    )

    response = _get(client, _list_url(consultation, question), non_staff_user_token)

    assert response.status_code == 200
    item = response.json()["all_respondents"][0]
    assert set(item) == RESPONSE_DETAIL_FIELDS
    assert "free_text_answer_text" not in item


@pytest.mark.django_db
def test_v2_response_list_keyword_search_matches_response_text(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(question=question, respondent=respondent, text="Infrastructure is crumbling")
    ResponseFactory(question=question, respondent=respondent, text="Bus services are failing")

    response = _get(
        client,
        f"{_list_url(consultation, question)}?searchValue=infrastructure&searchMode=keyword",
        non_staff_user_token,
    )

    assert response.status_code == 200
    results = response.json()["all_respondents"]
    assert len(results) == 1
    assert results[0]["text"] == "Infrastructure is crumbling"


@pytest.mark.django_db
def test_v2_response_list_includes_multiple_choice_answers(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, type="closed")
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(question=question, respondent=respondent, text="Yes", free_text=None)

    response = _get(client, _list_url(consultation, question), non_staff_user_token)

    assert response.status_code == 200
    results = response.json()["all_respondents"]
    assert [item["multiple_choice_answer"] for item in results] == [["Yes"]]


@pytest.mark.django_db
def test_v2_response_retrieve_demographic_data_from_demographic_responses(
    client, consultation, non_staff_user_token
):
    open_question = QuestionFactory(consultation=consultation, type="open")
    nation_question = QuestionFactory(consultation=consultation, type="demographic")
    age_question = QuestionFactory(consultation=consultation, type="demographic")
    respondent = RespondentFactory(consultation=consultation)
    answered = ResponseFactory(
        question=open_question, respondent=respondent, text="My main concern is flooding"
    )
    ResponseFactory(question=nation_question, respondent=respondent, text="England")
    ResponseFactory(question=age_question, respondent=respondent, text="18-35")
    # Blank demographic answers are not surfaced
    ResponseFactory(question=nation_question, respondent=respondent, text="")

    response = _get(
        client, _detail_url(consultation, open_question, answered), non_staff_user_token
    )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "My main concern is flooding"
    assert body["demographic_data"] == {nation_question.text: "England", age_question.text: "18-35"}


@pytest.mark.django_db
def test_v2_response_retrieve_demographic_data_scoped_to_consultation(
    client, consultation, non_staff_user_token
):
    other_consultation = ConsultationFactory()
    other_nation = QuestionFactory(consultation=other_consultation, type="demographic")
    open_question = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    answered = ResponseFactory(question=open_question, respondent=respondent, text="Hello")
    ResponseFactory(
        question=other_nation,
        respondent=RespondentFactory(consultation=other_consultation),
        text="Wales",
    )

    response = _get(
        client, _detail_url(consultation, open_question, answered), non_staff_user_token
    )

    assert response.status_code == 200
    assert response.json()["demographic_data"] == {}


@pytest.mark.django_db
def test_v2_response_list_scoped_to_requested_question(
    client, consultation, non_staff_user_token
):
    first = QuestionFactory(consultation=consultation, type="open")
    second = QuestionFactory(consultation=consultation, type="open")
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(question=first, respondent=respondent, text="First question answer")

    response = _get(client, _list_url(consultation, second), non_staff_user_token)

    assert response.status_code == 200
    assert response.json()["all_respondents"] == []


@pytest.mark.django_db
def test_v2_response_list_forbidden_for_unassigned_user(client, non_staff_user_token):
    other_consultation = ConsultationFactory()
    question = QuestionFactory(consultation=other_consultation, type="open")
    ResponseFactory(question=question, respondent=RespondentFactory(consultation=other_consultation))

    response = _get(client, _list_url(other_consultation, question), non_staff_user_token)

    assert response.status_code == 403


@pytest.mark.django_db
def test_v2_response_list_staff_sees_any_consultation(client, staff_user_token):
    other_consultation = ConsultationFactory()
    question = QuestionFactory(consultation=other_consultation, type="open")
    ResponseFactory(
        question=question,
        respondent=RespondentFactory(consultation=other_consultation),
        text="An answer",
    )

    response = _get(client, _list_url(other_consultation, question), staff_user_token)

    assert response.status_code == 200
    assert response.json()["total_count"] == 1


@pytest.mark.django_db
def test_v2_response_list_requires_authentication(client, consultation):
    question = QuestionFactory(consultation=consultation, type="open")
    ResponseFactory(question=question, respondent=RespondentFactory(consultation=consultation))

    response = _get(client, _list_url(consultation, question))

    assert response.status_code == 401
