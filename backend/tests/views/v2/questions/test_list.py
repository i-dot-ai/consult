import pytest
from django.urls import reverse

from consultations.models import Question
from factories import ConsultationFactory, QuestionFactory, RespondentFactory, ResponseFactory


def _list_url(consultation):
    return reverse("question-v2-list", kwargs={"consultation_pk": consultation.id})


@pytest.mark.django_db
def test_v2_question_list_returns_every_question_in_file_order(
    client, consultation, non_staff_user_token
):
    QuestionFactory(consultation=consultation, number=2, text="Second")
    QuestionFactory(consultation=consultation, number=1, text="First")

    response = client.get(
        _list_url(consultation), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list)
    assert [question["text"] for question in body] == ["First", "Second"]
    assert set(body[0]) == {
        "id",
        "number",
        "text",
        "type",
        "closed_question",
        "status",
        "response_count",
    }


@pytest.mark.django_db
def test_v2_question_list_counts_only_answered_responses(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, number=1)
    answered, blank, missing = (RespondentFactory(consultation=consultation) for _ in range(3))
    ResponseFactory(question=question, respondent=answered, text="An answer", free_text=None)
    ResponseFactory(question=question, respondent=blank, text="", free_text=None)
    ResponseFactory(question=question, respondent=missing, text=None, free_text=None)

    response = client.get(
        _list_url(consultation), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    assert response.status_code == 200
    assert response.json()[0]["response_count"] == 1


@pytest.mark.django_db
def test_v2_question_list_scoped_to_consultation(client, consultation, non_staff_user_token):
    QuestionFactory(consultation=consultation, number=1)
    QuestionFactory(consultation=ConsultationFactory(), number=1)

    response = client.get(
        _list_url(consultation), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_v2_question_list_fresh_upload_has_no_type(client, consultation, non_staff_user_token):
    QuestionFactory(consultation=consultation, number=1, type=None)

    response = client.get(
        _list_url(consultation), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    question = response.json()[0]
    assert question["type"] is None
    assert question["closed_question"] is None
    assert question["status"] == Question.ThemeStatus.DRAFT


@pytest.mark.django_db
def test_v2_question_list_forbidden_for_unassigned_user(client, non_staff_user_token):
    other_consultation = ConsultationFactory()
    QuestionFactory(consultation=other_consultation, number=1)

    response = client.get(
        _list_url(other_consultation), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_v2_question_list_staff_sees_any_consultation(client, staff_user_token):
    other_consultation = ConsultationFactory()
    QuestionFactory(consultation=other_consultation, number=1)

    response = client.get(
        _list_url(other_consultation), headers={"Authorization": f"Bearer {staff_user_token}"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_v2_question_list_requires_authentication(client, consultation):
    response = client.get(_list_url(consultation))

    assert response.status_code == 401
