import json

import pytest
from waffle.testutils import override_switch

from consultation_analyser.consultations.models import Consultation
from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_managing_consultations_via_support(django_app):
    # given I am an admin user
    user = UserFactory(email="email@example.com", is_staff=True)
    sign_in(django_app, user.email)

    # when I generate a dummy consultation
    consultations_page = django_app.get("/support/consultations/")
    consultations_page = consultations_page.form.submit("generate_dummy_consultation")

    latest_consultation = Consultation.objects.all().order_by("created_at").last()
    consultation_page = consultations_page.click(latest_consultation.name)

    # then I should be able to download the JSON
    json_download = consultation_page.forms[0].submit("download_json")
    exported_data = json.loads(json_download.text)
    assert exported_data["consultation"]["name"] == latest_consultation.name

    # and I should be able to delete the consultation
    confirmation_page = consultation_page.click("Delete this consultation")
    consultations_page = confirmation_page.form.submit("confirm_deletion").follow()

    assert "The consultation has been deleted" in consultations_page
