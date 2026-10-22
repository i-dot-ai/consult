import pytest
from django.urls import reverse

from consultations.models import Question, Response
from factories import ConsultationFactory, QuestionFactory, RespondentFactory, ResponseFactory


@pytest.mark.django_db
def test_v2_delete_removes_question_and_its_responses(
    client, question_detail_url, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, number=1)
    kept = QuestionFactory(consultation=consultation, number=2)
    respondent = RespondentFactory(consultation=consultation)
    ResponseFactory(
        question=question, respondent=respondent, text="Gone with the question", free_text=None
    )
    ResponseFactory(question=kept, respondent=respondent, text="Stays", free_text=None)

    response = client.delete(
        question_detail_url(question), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    assert response.status_code == 204
    assert not Question.objects.filter(pk=question.pk).exists()
    assert not Response.objects.filter(question=question).exists()
    assert Response.objects.filter(question=kept).count() == 1


@pytest.mark.django_db
def test_v2_delete_unlinks_open_questions_pointing_at_it(
    client, question_detail_url, consultation, non_staff_user_token
):
    closed = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.CLOSED)
    open_question = QuestionFactory(
        consultation=consultation,
        number=2,
        type=Question.QuestionType.OPEN,
        closed_question=closed,
    )

    response = client.delete(
        question_detail_url(closed), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    assert response.status_code == 204
    open_question.refresh_from_db()
    assert open_question.closed_question is None


@pytest.mark.django_db
def test_v2_delete_by_owner_not_assigned(
    client, question_detail_url, non_staff_user, non_staff_user_token
):
    consultation = ConsultationFactory(created_by=non_staff_user)
    question = QuestionFactory(consultation=consultation, number=1)

    response = client.delete(
        question_detail_url(question), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_v2_delete_by_staff_on_any_consultation(client, question_detail_url, staff_user_token):
    question = QuestionFactory(consultation=ConsultationFactory(), number=1)

    response = client.delete(
        question_detail_url(question), headers={"Authorization": f"Bearer {staff_user_token}"}
    )

    assert response.status_code == 204


@pytest.mark.django_db
def test_v2_delete_forbidden_for_unassigned_user(client, question_detail_url, non_staff_user_token):
    question = QuestionFactory(consultation=ConsultationFactory(), number=1)

    response = client.delete(
        question_detail_url(question), headers={"Authorization": f"Bearer {non_staff_user_token}"}
    )

    assert response.status_code == 403
    assert Question.objects.filter(pk=question.pk).exists()


@pytest.mark.django_db
def test_v2_delete_question_from_another_consultation_is_not_found(
    client, question_detail_url, consultation, non_staff_user_token
):
    foreign_question = QuestionFactory(consultation=ConsultationFactory(), number=1)
    url = reverse(
        "question-v2-detail",
        kwargs={"consultation_pk": consultation.id, "pk": foreign_question.id},
    )

    response = client.delete(url, headers={"Authorization": f"Bearer {non_staff_user_token}"})

    assert response.status_code == 404
    assert Question.objects.filter(pk=foreign_question.pk).exists()
