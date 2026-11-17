from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone

from consultations.models import Consultation
from factories import ConsultationFactory

pytestmark = pytest.mark.django_db

CONFIRM_URL_NAME = "admin:consultations_consultation_migrate_v1_confirm"
CHANGELIST_URL = "/admin/consultations/consultation/"


@pytest.fixture
def staff_client(client, staff_user):
    client.force_login(staff_user)
    return client


def _action_post(staff_client, consultation_ids: list[str], follow: bool = False):
    return staff_client.post(
        CHANGELIST_URL,
        {"action": "migrate_v1_consultation", "_selected_action": consultation_ids},
        follow=follow,
    )


def test_action_with_multiple_selections_warns(staff_client):
    consultations = [str(c.id) for c in ConsultationFactory.create_batch(2)]

    response = _action_post(staff_client, consultations, follow=True)

    assert response.status_code == 200
    assert b"exactly one consultation" in response.content


def test_action_single_selection_redirects_to_confirmation_page(staff_client):
    consultation = ConsultationFactory(is_v1=True)

    response = _action_post(staff_client, [str(consultation.id)])

    assert response.status_code == 302
    assert reverse(CONFIRM_URL_NAME, args=[consultation.id]) in response["Location"]


def test_confirmation_page_shows_audit_counts(staff_client):
    consultation = ConsultationFactory(is_v1=True)

    response = staff_client.get(reverse(CONFIRM_URL_NAME, args=[consultation.id]))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Confirm v1 to v2 migration" in content
    assert consultation.title in content
    assert "will become open questions" in content


def test_confirmation_page_reports_already_migrated(staff_client):
    consultation = ConsultationFactory(is_v1=True)
    consultation.migrated_at = timezone.now()
    consultation.save()

    response = staff_client.get(reverse(CONFIRM_URL_NAME, args=[consultation.id]))

    assert response.status_code == 200
    assert b"already migrated" in response.content


def test_confirmation_page_reports_existing_survey_provider(staff_client):
    consultation = ConsultationFactory(
        is_v1=False, data_source=Consultation.DataSource.CITIZEN_SPACE
    )

    response = staff_client.get(reverse(CONFIRM_URL_NAME, args=[consultation.id]))

    assert response.status_code == 200
    assert b"skip conversion" in response.content


def test_confirm_post_enqueues_job_once(staff_client):
    consultation = ConsultationFactory(is_v1=True)
    url = reverse(CONFIRM_URL_NAME, args=[consultation.id])

    with patch("consultations.admin.migrate_v1_consultation_job.delay") as delay:
        response = staff_client.post(url)

    assert response.status_code == 302
    assert response["Location"] == CHANGELIST_URL
    delay.assert_called_once_with(consultation.id)

