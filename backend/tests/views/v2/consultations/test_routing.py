from uuid import uuid4

import pytest
from django.test import override_settings
from django.urls import NoReverseMatch, resolve, reverse


def test_v2_upload_route_is_registered():
    consultation_id = uuid4()
    url = reverse("consultation-v2-upload", kwargs={"pk": consultation_id})

    assert url == f"/api/v2/consultations/{consultation_id}/upload/"
    assert resolve(url).view_name == "consultation-v2-upload"


def test_v2_deep_validation_route_is_registered():
    consultation_id = uuid4()
    url = reverse("consultation-v2-deep-validation", kwargs={"pk": consultation_id})

    assert url == f"/api/v2/consultations/{consultation_id}/deep_validation/"
    assert resolve(url).view_name == "consultation-v2-deep-validation"


def test_v2_demographic_routes_are_registered():
    consultation_id = uuid4()
    question_id = uuid4()
    option_id = uuid4()
    merge_url = reverse(
        "question-v2-merge-demographics",
        kwargs={"consultation_pk": consultation_id, "pk": question_id},
    )
    update_url = reverse(
        "demographic-option-v2-detail",
        kwargs={"consultation_pk": consultation_id, "pk": option_id},
    )

    assert merge_url == (
        f"/api/v2/consultations/{consultation_id}/questions/{question_id}/demographics/merge/"
    )
    assert resolve(merge_url).view_name == "question-v2-merge-demographics"
    assert update_url == f"/api/v2/consultations/{consultation_id}/demographics/{option_id}/"
    assert resolve(update_url).view_name == "demographic-option-v2-detail"


@pytest.mark.django_db
def test_v2_routes_absent_when_flag_off(client, reload_urlconf):
    with override_settings(DATA_SETUP_V2_ENABLED=False):
        reload_urlconf()

        assert client.get("/api/v2/consultations/").status_code == 404
        with pytest.raises(NoReverseMatch):
            reverse("consultation-v2-list")
