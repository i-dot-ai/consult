from uuid import uuid4

import pytest
from django.test import override_settings
from django.urls import NoReverseMatch, resolve, reverse


def test_v2_question_routes_are_registered():
    consultation_id, question_id = uuid4(), uuid4()

    list_url = reverse("question-v2-list", kwargs={"consultation_pk": consultation_id})
    detail_url = reverse(
        "question-v2-detail", kwargs={"consultation_pk": consultation_id, "pk": question_id}
    )

    assert list_url == f"/api/v2/consultations/{consultation_id}/questions/"
    assert detail_url == f"/api/v2/consultations/{consultation_id}/questions/{question_id}/"
    assert resolve(list_url).view_name == "question-v2-list"
    assert resolve(detail_url).view_name == "question-v2-detail"


@pytest.mark.django_db
def test_v2_question_routes_absent_when_flag_off(client, reload_urlconf):
    with override_settings(DATA_SETUP_V2_ENABLED=False):
        reload_urlconf()

        assert client.get(f"/api/v2/consultations/{uuid4()}/questions/").status_code == 404
        with pytest.raises(NoReverseMatch):
            reverse("question-v2-list", kwargs={"consultation_pk": uuid4()})
