import pytest

from consultation_analyser.consultations.models import Consultation
from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_managing_consultation_users_via_support(django_app):
    # given I am an admin user
    user = UserFactory(email="email@example.com", is_staff=True)
    user2 = UserFactory(email="email2222@example.com", is_staff=False)
    user3 = UserFactory(email="email3333@example.com", is_staff=False)

    sign_in(django_app, user.email)

    # when I generate a dummy consultation
    consultations_page = django_app.get("/support/consultations/")
    consultations_page = consultations_page.form.submit("generate_dummy_consultation")

    latest_consultation = Consultation.objects.all().order_by("created_at").last()
    consultation_page = consultations_page.click(latest_consultation.title)

    assert "email2222@example.com" not in consultation_page

    consultation_users_page = consultation_page.click("Add users")
    consultation_users_page.form["users"] = [user2.id, user3.id]

    consultation_page = consultation_users_page.form.submit().follow()

    assert "Users updated" in consultation_page
    assert "email2222@example.com" in consultation_page
    assert "email3333@example.com" in consultation_page
