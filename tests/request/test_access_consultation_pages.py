import pytest
from waffle.testutils import override_switch


@pytest.mark.django_db
@override_switch("CONSULTATION_PROCESSING", True)
def test_accessing_when_flag_is_on(client):
    assert client.get("/").status_code == 200
    assert client.get("/consultations").status_code == 200


@pytest.mark.django_db
@override_switch("CONSULTATION_PROCESSING", False)
def test_accessing_when_flag_is_off(client):
    assert client.get("/").status_code == 200
    assert client.get("/consultations").status_code == 404
