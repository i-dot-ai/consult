import pytest
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken

from consultations.models import Question, Response
from factories import ConsultationFactory, QuestionFactory, RespondentFactory, UserFactory


def merge_url(consultation, question):
    return reverse(
        "question-v2-merge-demographics",
        kwargs={"consultation_pk": consultation.id, "pk": question.id},
    )


def demographic_response(question, text):
    return Response.objects.create(
        question=question,
        respondent=RespondentFactory(consultation=question.consultation),
        text=text,
    )


@pytest.mark.django_db
def test_merge_demographics_updates_selected_response_text_only(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(
        consultation=consultation,
        type=Question.QuestionType.DEMOGRAPHIC,
    )
    selected = [
        demographic_response(question, "North East"),
        demographic_response(question, "North West"),
    ]
    unselected = demographic_response(question, "South")

    response = client.post(
        merge_url(consultation, question),
        data={
            "new_value": "North",
            "responses": [str(item.id) for item in selected],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "new_value": "North",
        "responses": [str(item.id) for item in selected],
    }
    assert set(
        Response.objects.filter(id__in=[item.id for item in selected]).values_list(
            "text", flat=True
        )
    ) == {"North"}
    assert Response.objects.get(id=unselected.id).text == "South"
    assert Response.objects.filter(id__in=[item.id for item in selected]).count() == 2


@pytest.mark.django_db
def test_merge_demographics_rejects_response_from_another_question(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(
        consultation=consultation,
        type=Question.QuestionType.DEMOGRAPHIC,
    )
    selected = demographic_response(question, "North")
    other_question = QuestionFactory(
        consultation=consultation,
        type=Question.QuestionType.DEMOGRAPHIC,
    )
    other = demographic_response(other_question, "South")

    response = client.post(
        merge_url(consultation, question),
        data={"new_value": "Merged", "responses": [str(selected.id), str(other.id)]},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    selected.refresh_from_db()
    other.refresh_from_db()
    assert selected.text == "North"
    assert other.text == "South"


@pytest.mark.django_db
def test_merge_demographics_rejects_non_demographic_question(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(
        consultation=consultation,
        type=Question.QuestionType.OPEN,
    )
    responses = [demographic_response(question, text) for text in ["First", "Second"]]

    response = client.post(
        merge_url(consultation, question),
        data={
            "new_value": "Merged",
            "responses": [str(item.id) for item in responses],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert list(
        Response.objects.filter(id__in=[item.id for item in responses])
        .order_by("text")
        .values_list("text", flat=True)
    ) == ["First", "Second"]


@pytest.mark.django_db
@pytest.mark.parametrize("responses", [[], ["one"], ["duplicate", "duplicate"]])
def test_merge_demographics_rejects_invalid_response_lists(
    client, consultation, non_staff_user_token, responses
):
    question = QuestionFactory(
        consultation=consultation,
        type=Question.QuestionType.DEMOGRAPHIC,
    )
    if responses == ["one"]:
        responses = [str(demographic_response(question, "North").id)]
    elif responses == ["duplicate", "duplicate"]:
        response_id = str(demographic_response(question, "North").id)
        responses = [response_id, response_id]

    response = client.post(
        merge_url(consultation, question),
        data={"new_value": "Merged", "responses": responses},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 400
    assert "responses" in response.json()


@pytest.mark.django_db
def test_merge_demographics_rejects_question_from_another_consultation(
    client, consultation, non_staff_user_token
):
    question = QuestionFactory(
        consultation=ConsultationFactory(),
        type=Question.QuestionType.DEMOGRAPHIC,
    )
    responses = [demographic_response(question, text) for text in ["First", "Second"]]

    response = client.post(
        merge_url(consultation, question),
        data={
            "new_value": "Merged",
            "responses": [str(item.id) for item in responses],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_merge_demographics_rejects_unassigned_user(client, consultation):
    question = QuestionFactory(
        consultation=consultation,
        type=Question.QuestionType.DEMOGRAPHIC,
    )
    responses = [demographic_response(question, text) for text in ["First", "Second"]]
    user = UserFactory(is_staff=False)
    token = str(RefreshToken.for_user(user).access_token)

    response = client.post(
        merge_url(consultation, question),
        data={
            "new_value": "Merged",
            "responses": [str(item.id) for item in responses],
        },
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
