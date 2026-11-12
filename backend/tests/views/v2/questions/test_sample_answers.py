import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from factories import (
    ConsultationFactory,
    QuestionFactory,
    RespondentFactory,
    ResponseFactory,
    UserFactory,
)


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def imported_response(question, text):
    return ResponseFactory(
        question=question,
        respondent=RespondentFactory(consultation=question.consultation),
        text=text,
        free_text=None,
    )


@pytest.mark.django_db
def test_sample_answers_returns_three_imported_answers_and_total_count(
    client, consultation, non_staff_user_token, sample_answers_url
):
    question = QuestionFactory(consultation=consultation)
    for text in ["First", "Second", "Third", "Fourth"]:
        imported_response(question, text)

    response = client.get(
        sample_answers_url(consultation, question),
        headers=auth(non_staff_user_token),
    )

    assert response.status_code == 200
    assert len(response.json()["answers"]) == 3
    assert set(response.json()["answers"]).issubset({"First", "Second", "Third", "Fourth"})
    assert response.json()["total_count"] == 4


@pytest.mark.django_db
def test_sample_answers_excludes_blank_and_other_question_responses(
    client, consultation, non_staff_user_token, sample_answers_url
):
    question = QuestionFactory(consultation=consultation)
    imported_response(question, "An answer")
    imported_response(question, "")
    imported_response(question, None)
    imported_response(QuestionFactory(consultation=consultation), "Another question")

    response = client.get(
        sample_answers_url(consultation, question),
        headers=auth(non_staff_user_token),
    )

    assert response.status_code == 200
    assert response.json() == {"answers": ["An answer"], "total_count": 1}


@pytest.mark.django_db
def test_sample_answers_rejects_question_from_another_consultation(
    client, consultation, non_staff_user_token, sample_answers_url
):
    question = QuestionFactory(consultation=ConsultationFactory())
    imported_response(question, "An answer")

    response = client.get(
        sample_answers_url(consultation, question),
        headers=auth(non_staff_user_token),
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_sample_answers_rejects_unassigned_user(client, consultation, sample_answers_url):
    question = QuestionFactory(consultation=consultation)
    imported_response(question, "An answer")
    token = str(RefreshToken.for_user(UserFactory(is_staff=False)).access_token)

    response = client.get(
        sample_answers_url(consultation, question),
        headers=auth(token),
    )

    assert response.status_code == 403
