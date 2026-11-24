from unittest.mock import patch

import pytest
from django.urls import reverse

from consultations.models import Consultation
from factories import ConsultationFactory, QuestionFactory


def find_themes_url(consultation):
    return reverse("consultation-v2-find-themes", kwargs={"pk": consultation.id})


@pytest.mark.django_db
def test_v2_find_themes_enqueues_worker(client, consultation, non_staff_user_token):
    QuestionFactory(consultation=consultation, number=1, type="open", has_free_text=False)

    with patch("consultations.api_v2.views.consultation.find_themes_job.enqueue") as enqueue:
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 202
    enqueue.assert_called_once_with(consultation.id, enqueue.call_args.args[1])
    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.FINDING_THEMES
    assert consultation.running_job == Consultation.RunningJob.FIND_THEMES


@pytest.mark.django_db
def test_v2_find_themes_rolls_back_when_enqueue_fails(client, consultation, non_staff_user_token):
    QuestionFactory(consultation=consultation, number=1, type="open")

    with patch(
        "consultations.api_v2.views.consultation.find_themes_job.enqueue",
        side_effect=RuntimeError("Redis unavailable"),
    ):
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 500
    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.SETUP
    assert consultation.running_job is None


@pytest.mark.django_db
def test_v2_find_themes_rejects_closed_questions(client, consultation, non_staff_user_token):
    QuestionFactory(consultation=consultation, number=1, type="closed", has_free_text=True)

    with patch("consultations.api_v2.views.consultation.find_themes_job.enqueue") as enqueue:
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    enqueue.assert_not_called()


@pytest.mark.django_db
def test_v2_find_themes_rejects_consultations_not_in_setup_stage(
    client, non_staff_user, non_staff_user_token
):
    consultation = ConsultationFactory(code="in-progress", stage=Consultation.Stage.FINDING_THEMES)
    consultation.users.add(non_staff_user)

    with patch("consultations.api_v2.views.consultation.find_themes_job.enqueue") as enqueue:
        response = client.post(
            find_themes_url(consultation),
            headers={"Authorization": f"Bearer {non_staff_user_token}"},
        )

    assert response.status_code == 400
    enqueue.assert_not_called()
