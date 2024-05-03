import pytest
from waffle.testutils import override_switch

from consultation_analyser.factories import ConsultationFactory, UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
@override_switch("FRONTEND_USER_LOGIN", True)
def test_user_can_see_consultations(django_app):
    # given i am a user without consultations
    user = UserFactory(email="email@example.com", password="admin")  # pragma: allowlist secret

    # when i sign in
    landing_page = sign_in(django_app, "email@example.com")

    # then i should see an empty state on the landing page
    assert "You do not have any consultations" in landing_page

    # but when i add a consultation
    consultation = ConsultationFactory(name="My First Consultation", user=user)

    # and i sign in again
    landing_page.click("Sign out")
    landing_page = sign_in(django_app, "email@example.com")

    # then i should see the new consultation
    assert "My First Consultation" in landing_page
