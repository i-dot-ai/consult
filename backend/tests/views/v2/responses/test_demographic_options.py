import uuid

import pytest
from django.urls import reverse

from consultations.api_v2.demographic_tokens import (
    decode_demographic_token,
    encode_demographic_token,
)
from factories import QuestionFactory, RespondentFactory, ResponseFactory


def _options_url(consultation):
    return reverse(
        "response-v2-demographic-options", kwargs={"consultation_pk": consultation.id}
    )


def _list_url(consultation, question):
    return reverse(
        "question-response-v2-list", kwargs={"consultation_pk": consultation.id, "question_pk": question.id}
    )


def _get(client, url, token):
    return client.get(url, headers={"Authorization": f"Bearer {token}"})


def test_demographic_token_round_trips_arbitrary_values():
    question_id = str(uuid.uuid4())
    value = "England & Wales: 18–35 / «quote»"

    token = encode_demographic_token(question_id, value)

    assert decode_demographic_token(token) == (question_id, value)


def test_malformed_demographic_tokens_decode_to_none():
    assert decode_demographic_token("") is None
    assert decode_demographic_token("!!!not-base64!!!") is None
    assert decode_demographic_token("bm90LWFfdG9rZW4") is None  # valid base64, not a token


@pytest.mark.django_db
def test_demographic_options_grouped_by_question_with_respondent_counts(
    client, consultation, non_staff_user_token
):
    open_question = QuestionFactory(consultation=consultation, type="open", number=1)
    nation = QuestionFactory(consultation=consultation, type="demographic", number=2)
    age = QuestionFactory(consultation=consultation, type="demographic", number=3)
    r1, r2, r3 = (RespondentFactory(consultation=consultation) for _ in range(3))
    for respondent in (r1, r2, r3):
        ResponseFactory(question=open_question, respondent=respondent, text="My view")
    ResponseFactory(question=nation, respondent=r1, text="England")
    ResponseFactory(question=nation, respondent=r2, text="England")
    ResponseFactory(question=nation, respondent=r3, text="Wales")
    ResponseFactory(question=age, respondent=r1, text="18-35")
    # A respondent whose only answers are demographic still counts when no
    # filter narrows the response set
    ResponseFactory(
        question=nation, respondent=RespondentFactory(consultation=consultation), text="Scotland"
    )
    # Blank demographic answers are ignored
    ResponseFactory(question=nation, respondent=r2, text="")

    response = _get(client, _options_url(consultation), non_staff_user_token)

    assert response.status_code == 200
    items = response.json()
    assert all(set(item) == {"id", "name", "value", "count"} for item in items)
    counts = {}
    for item in items:
        question_id, value = decode_demographic_token(item["id"])
        assert str(nation.id) == question_id or str(age.id) == question_id
        assert item["name"] == (nation.text if question_id == str(nation.id) else age.text)
        counts[(item["name"], value)] = item["count"]
    assert counts == {
        (nation.text, "England"): 2,
        (nation.text, "Wales"): 1,
        (nation.text, "Scotland"): 1,
        (age.text, "18-35"): 1,
    }


@pytest.mark.django_db
def test_demographic_options_follow_current_search_filters(
    client, consultation, non_staff_user_token
):
    open_question = QuestionFactory(consultation=consultation, type="open")
    nation = QuestionFactory(consultation=consultation, type="demographic")
    r1, r2 = RespondentFactory(consultation=consultation), RespondentFactory(consultation=consultation)
    ResponseFactory(question=open_question, respondent=r1, text="flooding worries me")
    ResponseFactory(question=open_question, respondent=r2, text="bus cuts hurt")
    ResponseFactory(question=nation, respondent=r1, text="England")
    ResponseFactory(question=nation, respondent=r2, text="Wales")

    response = _get(
        client,
        f"{_options_url(consultation)}?searchValue=flooding&searchMode=keyword",
        non_staff_user_token,
    )

    assert response.status_code == 200
    items = response.json()
    assert [(item["name"], item["value"], item["count"]) for item in items] == [
        (nation.text, "England", 1),
        (nation.text, "Wales", 0),
    ]


@pytest.mark.django_db
def test_demographic_options_scope_to_question_filter(
    client, consultation, non_staff_user_token
):
    first_question = QuestionFactory(consultation=consultation, type="open", number=1)
    second_question = QuestionFactory(consultation=consultation, type="open", number=2)
    nation = QuestionFactory(consultation=consultation, type="demographic", number=3)
    r1, r2 = RespondentFactory(consultation=consultation), RespondentFactory(consultation=consultation)
    ResponseFactory(question=first_question, respondent=r1, text="answer one")
    ResponseFactory(question=second_question, respondent=r2, text="answer two")
    ResponseFactory(question=nation, respondent=r1, text="England")
    ResponseFactory(question=nation, respondent=r2, text="Wales")

    response = _get(
        client,
        f"{_options_url(consultation)}?question_id={second_question.id}",
        non_staff_user_token,
    )

    assert response.status_code == 200
    items = response.json()
    assert [(item["name"], item["value"], item["count"]) for item in items] == [
        (nation.text, "Wales", 1),
        (nation.text, "England", 0),
    ]


@pytest.mark.django_db
def test_demographics_filter_passes_tokens_or_within_question_and_across_questions(
    client, consultation, non_staff_user_token
):
    open_question = QuestionFactory(consultation=consultation, type="open", number=1)
    nation = QuestionFactory(consultation=consultation, type="demographic", number=2)
    age = QuestionFactory(consultation=consultation, type="demographic", number=3)
    r1, r2, r3 = (RespondentFactory(consultation=consultation) for _ in range(3))
    for respondent in (r1, r2, r3):
        ResponseFactory(question=open_question, respondent=respondent, text="view")
    ResponseFactory(question=nation, respondent=r1, text="England")
    ResponseFactory(question=nation, respondent=r2, text="England")
    ResponseFactory(question=nation, respondent=r3, text="Wales")
    ResponseFactory(question=age, respondent=r1, text="18-35")

    url = _list_url(consultation, open_question)
    england = encode_demographic_token(nation.id, "England")
    wales = encode_demographic_token(nation.id, "Wales")
    young = encode_demographic_token(age.id, "18-35")

    # OR within a question group
    response = _get(client, f"{url}?demographics={england},{wales}", non_staff_user_token)
    assert len(response.json()["all_respondents"]) == 3

    # AND across question groups: only r1 is England and 18-35
    response = _get(
        client, f"{url}?demographics={england},{young}", non_staff_user_token
    )
    assert len(response.json()["all_respondents"]) == 1

    # Malformed tokens are ignored rather than filtering everything out
    response = _get(client, f"{url}?demographics=nonsense-token", non_staff_user_token)
    assert len(response.json()["all_respondents"]) == 3
