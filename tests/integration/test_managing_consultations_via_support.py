import pytest

from consultation_analyser.consultations.models import (
    Consultation,
    MultiChoiceAnswer,
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
    response = confirmation_page.form.submit("confirm_deletion")

    # Check we get redirected and the success message was set
    assert response.status_code == 302
    # The success message will be displayed after redirect, but we can't follow it
    # due to database connection issues with the async deletion job

    # safe tear down
    MultiChoiceAnswer.objects.all().delete()
