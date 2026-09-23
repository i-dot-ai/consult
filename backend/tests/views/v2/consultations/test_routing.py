import pytest
from django.test import override_settings
from django.urls import NoReverseMatch, reverse


@pytest.mark.django_db
def test_v2_routes_absent_when_flag_off(client, reload_urlconf):
    with override_settings(DATA_SETUP_V2_ENABLED=False):
        reload_urlconf()

        assert client.get("/api/v2/consultations/").status_code == 404
        with pytest.raises(NoReverseMatch):
            reverse("consultation-v2-list")
