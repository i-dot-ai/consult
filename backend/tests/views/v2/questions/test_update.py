import pytest

from consultations.models import Consultation, Question
from factories import ConsultationFactory, QuestionFactory


def _patch(client, question_detail_url, question, token, data):
    return client.patch(
        question_detail_url(question),
        data=data,
        content_type="application/json",
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.mark.django_db
def test_v2_update_sets_type_and_marks_question_configured(
    client, question_detail_url, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, number=1, type=None)

    response = _patch(
        client, question_detail_url, question, non_staff_user_token, {"type": "closed"}
    )

    assert response.status_code == 200
    assert response.json()["type"] == "closed"
    assert response.json()["status"] == Question.ThemeStatus.CONFIGURED
    question.refresh_from_db()
    assert question.type == Question.QuestionType.CLOSED
    assert question.status == Question.ThemeStatus.CONFIGURED
    consultation.refresh_from_db()
    assert consultation.survey_import_status == Consultation.SurveyImportStatus.IMPORT_COMPLETE


@pytest.mark.django_db
def test_v2_update_keeps_consultation_pending_until_all_questions_configured(
    client, question_detail_url, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, number=1, type=None)
    QuestionFactory(consultation=consultation, number=2, type=None)

    response = _patch(
        client, question_detail_url, question, non_staff_user_token, {"type": "closed"}
    )

    assert response.status_code == 200
    consultation.refresh_from_db()
    assert consultation.survey_import_status == Consultation.SurveyImportStatus.PENDING_QUESTIONS


@pytest.mark.django_db
def test_v2_update_rewords_question(
    client, question_detail_url, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, number=1, text="Do you agree?")

    response = _patch(
        client,
        question_detail_url,
        question,
        non_staff_user_token,
        {"text": "Do you agree with the zoning plan?"},
    )

    assert response.status_code == 200
    question.refresh_from_db()
    assert question.text == "Do you agree with the zoning plan?"


@pytest.mark.django_db
def test_v2_update_rejects_blank_wording(
    client, question_detail_url, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, number=1, text="Original")

    response = _patch(client, question_detail_url, question, non_staff_user_token, {"text": "   "})

    assert response.status_code == 400
    assert "text" in response.json()
    question.refresh_from_db()
    assert question.text == "Original"


@pytest.mark.django_db
@pytest.mark.parametrize("value", ["hybrid", ""])
def test_v2_update_rejects_unknown_or_blank_type(
    client, question_detail_url, consultation, non_staff_user_token, value
):
    question = QuestionFactory(consultation=consultation, number=1, type=None)

    response = _patch(client, question_detail_url, question, non_staff_user_token, {"type": value})

    assert response.status_code == 400
    assert "type" in response.json()
    question.refresh_from_db()
    assert question.status == Question.ThemeStatus.DRAFT


@pytest.mark.django_db
def test_v2_update_clears_type_with_null(
    client, question_detail_url, consultation, non_staff_user_token
):
    question = QuestionFactory(
        consultation=consultation,
        number=1,
        type=Question.QuestionType.OPEN,
        status=Question.ThemeStatus.CONFIGURED,
    )

    response = _patch(client, question_detail_url, question, non_staff_user_token, {"type": None})

    assert response.status_code == 200
    question.refresh_from_db()
    assert question.type is None
    assert question.status == Question.ThemeStatus.DRAFT
    consultation.refresh_from_db()
    assert consultation.survey_import_status == Consultation.SurveyImportStatus.PENDING_QUESTIONS


@pytest.mark.django_db
def test_v2_update_links_open_question_to_closed_question(
    client, question_detail_url, consultation, non_staff_user_token
):
    closed = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.CLOSED)
    open_question = QuestionFactory(
        consultation=consultation, number=2, type=Question.QuestionType.OPEN
    )

    response = _patch(
        client,
        question_detail_url,
        open_question,
        non_staff_user_token,
        {"closed_question": str(closed.id)},
    )

    assert response.status_code == 200
    assert response.json()["closed_question"] == str(closed.id)
    open_question.refresh_from_db()
    assert open_question.closed_question == closed


@pytest.mark.django_db
def test_v2_update_sets_type_and_link_together(
    client, question_detail_url, consultation, non_staff_user_token
):
    closed = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.CLOSED)
    question = QuestionFactory(consultation=consultation, number=2, type=None)

    response = _patch(
        client,
        question_detail_url,
        question,
        non_staff_user_token,
        {"type": "open", "closed_question": str(closed.id)},
    )

    assert response.status_code == 200
    question.refresh_from_db()
    assert question.type == Question.QuestionType.OPEN
    assert question.closed_question == closed


@pytest.mark.django_db
def test_v2_update_unlinks_with_null(
    client, question_detail_url, consultation, non_staff_user_token
):
    closed = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.CLOSED)
    open_question = QuestionFactory(
        consultation=consultation,
        number=2,
        type=Question.QuestionType.OPEN,
        closed_question=closed,
    )

    response = _patch(
        client, question_detail_url, open_question, non_staff_user_token, {"closed_question": None}
    )

    assert response.status_code == 200
    open_question.refresh_from_db()
    assert open_question.closed_question is None


@pytest.mark.django_db
def test_v2_update_rejects_link_to_open_question(
    client, question_detail_url, consultation, non_staff_user_token
):
    other_open = QuestionFactory(
        consultation=consultation, number=1, type=Question.QuestionType.OPEN
    )
    question = QuestionFactory(consultation=consultation, number=2, type=Question.QuestionType.OPEN)

    response = _patch(
        client,
        question_detail_url,
        question,
        non_staff_user_token,
        {"closed_question": str(other_open.id)},
    )

    assert response.status_code == 400
    assert "closed_question" in response.json()


@pytest.mark.django_db
def test_v2_update_rejects_link_from_closed_question(
    client, question_detail_url, consultation, non_staff_user_token
):
    target = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.CLOSED)
    question = QuestionFactory(
        consultation=consultation, number=2, type=Question.QuestionType.CLOSED
    )

    response = _patch(
        client,
        question_detail_url,
        question,
        non_staff_user_token,
        {"closed_question": str(target.id)},
    )

    assert response.status_code == 400
    assert "closed_question" in response.json()


@pytest.mark.django_db
def test_v2_update_rejects_turning_linked_open_question_closed(
    client, question_detail_url, consultation, non_staff_user_token
):
    closed = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.CLOSED)
    linked = QuestionFactory(
        consultation=consultation,
        number=2,
        type=Question.QuestionType.OPEN,
        closed_question=closed,
    )

    response = _patch(client, question_detail_url, linked, non_staff_user_token, {"type": "closed"})

    assert response.status_code == 400
    assert "closed_question" in response.json()
    linked.refresh_from_db()
    assert linked.type == Question.QuestionType.OPEN


@pytest.mark.django_db
def test_v2_update_retyping_closed_question_clears_links_to_it(
    client, question_detail_url, consultation, non_staff_user_token
):
    closed = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.CLOSED)
    linked = QuestionFactory(
        consultation=consultation,
        number=2,
        type=Question.QuestionType.OPEN,
        closed_question=closed,
    )
    other = QuestionFactory(consultation=consultation, number=3, type=Question.QuestionType.CLOSED)
    linked_to_other = QuestionFactory(
        consultation=consultation,
        number=4,
        type=Question.QuestionType.OPEN,
        closed_question=other,
    )

    response = _patch(client, question_detail_url, closed, non_staff_user_token, {"type": "open"})

    assert response.status_code == 200
    linked.refresh_from_db()
    assert linked.closed_question is None
    linked_to_other.refresh_from_db()
    assert linked_to_other.closed_question == other


@pytest.mark.django_db
def test_v2_update_rewording_closed_question_keeps_links_to_it(
    client, question_detail_url, consultation, non_staff_user_token
):
    closed = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.CLOSED)
    linked = QuestionFactory(
        consultation=consultation,
        number=2,
        type=Question.QuestionType.OPEN,
        closed_question=closed,
    )

    response = _patch(
        client, question_detail_url, closed, non_staff_user_token, {"text": "Reworded"}
    )

    assert response.status_code == 200
    linked.refresh_from_db()
    assert linked.closed_question == closed


@pytest.mark.django_db
def test_v2_update_rejects_link_across_consultations(
    client, question_detail_url, consultation, non_staff_user_token
):
    foreign_closed = QuestionFactory(
        consultation=ConsultationFactory(), number=1, type=Question.QuestionType.CLOSED
    )
    question = QuestionFactory(consultation=consultation, number=1, type=Question.QuestionType.OPEN)

    response = _patch(
        client,
        question_detail_url,
        question,
        non_staff_user_token,
        {"closed_question": str(foreign_closed.id)},
    )

    assert response.status_code == 400
    assert "closed_question" in response.json()


@pytest.mark.django_db
def test_v2_update_rejects_self_link(
    client, question_detail_url, consultation, non_staff_user_token
):
    question = QuestionFactory(
        consultation=consultation, number=1, type=Question.QuestionType.CLOSED
    )

    response = _patch(
        client,
        question_detail_url,
        question,
        non_staff_user_token,
        {"closed_question": str(question.id)},
    )

    assert response.status_code == 400
    assert "closed_question" in response.json()


@pytest.mark.django_db
def test_v2_update_ignores_read_only_fields(
    client, question_detail_url, consultation, non_staff_user_token
):
    question = QuestionFactory(consultation=consultation, number=3)

    response = _patch(
        client,
        question_detail_url,
        question,
        non_staff_user_token,
        {"number": 9, "status": "confirmed", "type": "open"},
    )

    assert response.status_code == 200
    question.refresh_from_db()
    assert question.number == 3
    assert question.status == Question.ThemeStatus.CONFIGURED


@pytest.mark.django_db
def test_v2_update_forbidden_for_unassigned_user(client, question_detail_url, non_staff_user_token):
    question = QuestionFactory(consultation=ConsultationFactory(), number=1)

    response = _patch(client, question_detail_url, question, non_staff_user_token, {"type": "open"})

    assert response.status_code == 403


@pytest.mark.django_db
def test_v2_update_put_not_allowed(client, question_detail_url, consultation, non_staff_user_token):
    question = QuestionFactory(consultation=consultation, number=1)

    response = client.put(
        question_detail_url(question),
        data={"type": "open"},
        content_type="application/json",
        headers={"Authorization": f"Bearer {non_staff_user_token}"},
    )

    assert response.status_code == 405
