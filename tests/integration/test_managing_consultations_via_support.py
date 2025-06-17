import pytest

from consultation_analyser.consultations.models import (
    Consultation,
)
from consultation_analyser.factories import (
    UserFactory,
)
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
    consultation_page = consultations_page.click(latest_consultation.title)

    # and I should be able to delete the consultation
    confirmation_page = consultation_page.click("Delete this consultation")
    consultations_page = confirmation_page.form.submit("confirm_deletion").follow()

    assert "The consultation has been sent for deletion" in consultations_page
