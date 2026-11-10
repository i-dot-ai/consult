from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import serializers

from consultations.models import Consultation, Question
from factories import ConsultationFactory, QuestionFactory


def find_themes_url(consultation):
    return reverse("consultation-v2-find-themes", kwargs={"pk": consultation.id})


@pytest.mark.django_db
def test_v2_find_themes_assigns_code_and_mirrors_inputs(client, consultation, non_staff_user_token):
    consultation.code = ""
    consultation.save(update_fields=["code"])
    QuestionFactory(consultation=consultation, number=1, type="open")

    with (
        patch("consultations.api_v2.views.consultation.export_consultation_inputs_to_s3") as export,
        patch("consultations.api_v2.views.consultation.batch.submit_job") as submit_job,
    ):
        export.return_value = 1
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 202
    consultation.refresh_from_db()
    assert consultation.code  # a code was assigned and persisted
    export.assert_called_once_with(consultation, consultation.code)
    submit_job.assert_called_once()
    assert submit_job.call_args.kwargs["consultation_code"] == consultation.code
    assert response.json()["consultation_code"] == consultation.code
    assert consultation.stage == Consultation.Stage.FINDING_THEMES


@pytest.mark.django_db
def test_v2_find_themes_reuses_an_existing_code(client, consultation, non_staff_user_token):
    QuestionFactory(consultation=consultation, number=1, type="open")

    with (
        patch("consultations.api_v2.views.consultation.assign_consultation_code") as assign,
        patch("consultations.api_v2.views.consultation.export_consultation_inputs_to_s3") as export,
        patch("consultations.api_v2.views.consultation.batch.submit_job") as submit_job,
    ):
        assign.return_value = consultation.code
        export.return_value = 1
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 202
    assert assign.call_args.args[0] == consultation
    export.assert_called_once_with(consultation, "my-first-consultation")
    submit_job.assert_called_once()
    assert submit_job.call_args.kwargs["consultation_code"] == "my-first-consultation"


@pytest.mark.django_db
def test_v2_find_themes_does_not_submit_the_batch_when_mirroring_fails(
    client, consultation, non_staff_user_token
):
    QuestionFactory(consultation=consultation, number=1, type="open")

    with (
        patch(
            "consultations.api_v2.views.consultation.export_consultation_inputs_to_s3",
            side_effect=RuntimeError("S3 unavailable"),
        ),
        patch("consultations.api_v2.views.consultation.batch.submit_job") as submit_job,
    ):
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 500
    submit_job.assert_not_called()
    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.SETUP


@pytest.mark.django_db
def test_v2_find_themes_rolls_the_stage_back_when_the_submission_fails(
    client, consultation, non_staff_user_token
):
    QuestionFactory(consultation=consultation, number=1, type="open")

    with (
        patch("consultations.api_v2.views.consultation.export_consultation_inputs_to_s3") as export,
        patch(
            "consultations.api_v2.views.consultation.batch.submit_job", side_effect=RuntimeError
        ) as submit_job,
    ):
        export.return_value = 1
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 500
    submit_job.assert_called_once()
    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.SETUP  # retryable


@pytest.mark.django_db
def test_v2_find_themes_does_not_mask_drf_permission_errors_as_500(client, non_staff_user_token):
    """Consultations outside a user's visibility fail CanSeeConsultationV2
    before the action runs - that 403 must survive, as must any Http404 or
    APIException raised inside the action body (no 500 masking)."""

    with patch("consultations.api_v2.views.consultation.batch.submit_job") as submit_job:
        response = client.post(
            reverse(
                "consultation-v2-find-themes",
                kwargs={"pk": "00000000-0000-0000-0000-000000000000"},
            ),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 403
    submit_job.assert_not_called()


@pytest.mark.django_db
def test_v2_find_themes_lets_api_exceptions_surface(client, consultation, non_staff_user_token):
    QuestionFactory(consultation=consultation, number=1, type="open")

    with (
        patch(
            "consultations.api_v2.views.consultation.export_consultation_inputs_to_s3",
            side_effect=serializers.ValidationError("bad consultation data"),
        ),
        patch("consultations.api_v2.views.consultation.batch.submit_job") as submit_job,
    ):
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    assert "bad consultation data" in response.json()
    submit_job.assert_not_called()


@pytest.mark.django_db
def test_v2_find_themes_syncs_flags_before_the_guard(client, consultation, non_staff_user_token):
    """A closed question carrying a stale free-text flag must not pass the guard."""
    consultation.code = ""
    consultation.save(update_fields=["code"])
    closed_question = QuestionFactory(
        consultation=consultation, number=1, type="closed", has_free_text=True
    )

    with (
        patch("consultations.api_v2.views.consultation.assign_consultation_code") as assign,
        patch("consultations.api_v2.views.consultation.export_consultation_inputs_to_s3") as export,
        patch("consultations.api_v2.views.consultation.batch.submit_job") as submit_job,
    ):
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    assert "no free-text questions" in response.json()["error"]
    closed_question.refresh_from_db()
    assert closed_question.has_free_text is False
    assign.assert_not_called()
    export.assert_not_called()
    submit_job.assert_not_called()


@pytest.mark.django_db
def test_v2_find_themes_passes_the_guard_after_syncing(client, consultation, non_staff_user_token):
    """A question typed open with a stale flag becomes findable via the sync."""
    QuestionFactory(consultation=consultation, number=1, type="open", has_free_text=False)

    with (
        patch("consultations.api_v2.views.consultation.assign_consultation_code") as assign,
        patch("consultations.api_v2.views.consultation.export_consultation_inputs_to_s3") as export,
        patch("consultations.api_v2.views.consultation.batch.submit_job") as submit_job,
    ):
        assign.return_value = consultation.code
        export.return_value = 1
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 202
    question = Question.objects.get(consultation=consultation)
    assert question.has_free_text is True
    export.assert_called_once_with(consultation, "my-first-consultation")
    submit_job.assert_called_once()


@pytest.mark.django_db
def test_v2_find_themes_rejects_consultations_not_in_setup_stage(
    client, non_staff_user, non_staff_user_token
):
    consultation = ConsultationFactory(code="in-progress", stage=Consultation.Stage.FINDING_THEMES)
    consultation.users.add(non_staff_user)

    with (
        patch("consultations.api_v2.views.consultation.assign_consultation_code") as assign,
        patch("consultations.api_v2.views.consultation.export_consultation_inputs_to_s3") as export,
        patch("consultations.api_v2.views.consultation.batch.submit_job") as submit_job,
    ):
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    assert "not in setup stage" in response.json()["error"]
    assign.assert_not_called()
    export.assert_not_called()
    submit_job.assert_not_called()
