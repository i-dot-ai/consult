import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import Question
from factories import ConsultationFactory, QuestionFactory, UserFactory


def demographic_question(consultation):
    return QuestionFactory(consultation=consultation, type=Question.QuestionType.DEMOGRAPHIC)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.django_db
def test_demographics_groups_answers_by_text_with_counts_and_response_ids(
    client, consultation, non_staff_user_token, demographics_url, demographic_response
):
    question = demographic_question(consultation)
    north = [
        demographic_response(question, "North"),
        demographic_response(question, "North"),
    ]
    south = [
        demographic_response(question, "South"),
        demographic_response(question, "South"),
        demographic_response(question, "South"),
    ]
    east = demographic_response(question, "East")
    demographic_response(demographic_question(consultation), "North")

    response = client.get(
        demographics_url(consultation, question), headers=auth(non_staff_user_token)
    )

    assert response.status_code == 200
    answers = response.json()
    assert [(answer["text"], answer["count"]) for answer in answers] == [
        ("South", 3),
        ("North", 2),
        ("East", 1),
    ]
    assert set(answers[0]["responses"]) == {str(item.id) for item in south}
    assert set(answers[1]["responses"]) == {str(item.id) for item in north}
    assert answers[2]["responses"] == [str(east.id)]


@pytest.mark.django_db
def test_demographics_excludes_blank_answers(
    client, consultation, non_staff_user_token, demographics_url, demographic_response
):
    question = demographic_question(consultation)
    answered = demographic_response(question, "North")
    demographic_response(question, "")
    demographic_response(question, None)

    response = client.get(
        demographics_url(consultation, question), headers=auth(non_staff_user_token)
    )

    assert response.status_code == 200
    assert response.json() == [{"text": "North", "count": 1, "responses": [str(answered.id)]}]


@pytest.mark.django_db
def test_demographics_returns_empty_list_for_unanswered_question(
    client, consultation, non_staff_user_token, demographics_url
):
    question = demographic_question(consultation)

    response = client.get(
        demographics_url(consultation, question), headers=auth(non_staff_user_token)
    )

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.django_db
def test_demographics_rejects_open_question(
    client, consultation, non_staff_user_token, demographics_url, demographic_response
):
    question = QuestionFactory(consultation=consultation, type=Question.QuestionType.OPEN)
    demographic_response(question, "Free text")

    response = client.get(
        demographics_url(consultation, question), headers=auth(non_staff_user_token)
    )

    assert response.status_code == 400
    assert "question" in response.json()


@pytest.mark.django_db
def test_demographics_rejects_question_from_another_consultation(
    client, consultation, non_staff_user_token, demographics_url, demographic_response
):
    question = demographic_question(ConsultationFactory())
    demographic_response(question, "North")

    response = client.get(
        demographics_url(consultation, question), headers=auth(non_staff_user_token)
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_demographics_allows_staff_user(
    client, consultation, staff_user_token, demographics_url, demographic_response
):
    question = demographic_question(consultation)
    answered = demographic_response(question, "North")

    response = client.get(demographics_url(consultation, question), headers=auth(staff_user_token))

    assert response.status_code == 200
    assert response.json() == [{"text": "North", "count": 1, "responses": [str(answered.id)]}]


@pytest.mark.django_db
def test_demographics_allows_consultation_owner(client, demographics_url, demographic_response):
    owner = UserFactory(is_staff=False)
    consultation = ConsultationFactory(created_by=owner)
    question = demographic_question(consultation)
    answered = demographic_response(question, "North")
    token = str(RefreshToken.for_user(owner).access_token)

    response = client.get(demographics_url(consultation, question), headers=auth(token))

    assert response.status_code == 200
    assert response.json() == [{"text": "North", "count": 1, "responses": [str(answered.id)]}]


@pytest.mark.django_db
def test_demographics_rejects_unassigned_user(
    client, consultation, demographics_url, demographic_response
):
    question = demographic_question(consultation)
    demographic_response(question, "North")
    token = str(RefreshToken.for_user(UserFactory(is_staff=False)).access_token)

    response = client.get(demographics_url(consultation, question), headers=auth(token))

    assert response.status_code == 403


@pytest.mark.django_db
def test_demographics_response_ids_are_accepted_by_merge(
    client, consultation, non_staff_user_token, demographics_url, merge_url, demographic_response
):
    question = demographic_question(consultation)
    for text in ["North East", "North West", "South"]:
        demographic_response(question, text)
    headers = auth(non_staff_user_token)

    answers = client.get(demographics_url(consultation, question), headers=headers).json()
    to_merge = [answer for answer in answers if answer["text"].startswith("North")]
    merged = client.post(
        merge_url(consultation, question),
        data={
            "new_value": "North",
            "responses": [
                response_id for answer in to_merge for response_id in answer["responses"]
            ],
        },
        content_type="application/json",
        headers=headers,
    )
    assert merged.status_code == 200

    response = client.get(demographics_url(consultation, question), headers=headers)

    assert [(answer["text"], answer["count"]) for answer in response.json()] == [
        ("North", 2),
        ("South", 1),
    ]


@pytest.mark.django_db
def test_demographics_lists_answers_to_a_closed_question(
    client, consultation, non_staff_user_token, demographics_url, demographic_response
):
    question = QuestionFactory(consultation=consultation, type=Question.QuestionType.CLOSED)
    answered = demographic_response(question, "Yes")

    response = client.get(
        demographics_url(consultation, question), headers=auth(non_staff_user_token)
    )

    assert response.status_code == 200
    assert response.json() == [{"text": "Yes", "count": 1, "responses": [str(answered.id)]}]
