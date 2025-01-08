import pytest

from consultation_analyser.factories2 import Consultation2Factory, UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_user_can_see_consultations(django_app):
    # given i am a user without consultations
    user = UserFactory(email="email@example.com", password="admin")  # pragma: allowlist secret

    # when i sign in
    landing_page = sign_in(django_app, "email@example.com")

    # then i should see an empty state on the landing page
    assert "You do not have any consultations" in landing_page

    # but when i add a consultation
    consultation = Consultation2Factory(text="My First Consultation")
    consultation.users.add(user)

    # and i sign in again
    landing_page.click("Sign out")
    landing_page = sign_in(django_app, "email@example.com")

    # then i should see the new consultation
    assert "My First Consultation" in landing_page


@pytest.mark.django_db
def test_logged_out_user_sees_404s(django_app):
    Consultation2Factory(slug="whatever")

    returned_page = django_app.get("/consultations/whatever/", expect_errors=True)

    assert "Page not found" in returned_page
