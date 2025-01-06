import pytest

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations.models import Consultation
from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_adding_users_to_consultations_via_support(django_app):
    # given I am an admin user
    user = UserFactory(
        email="email@example.com",
        is_staff=True,
    )
    sign_in(django_app, user.email)

    # when I generate a dummy consultation
    consultations_index = django_app.get("/support/consultations/")
    consultations_index = consultations_index.form.submit("generate_dummy_consultation")

    latest_consultation = Consultation.objects.all().order_by("created_at").last()
    consultation_page = consultations_index.click(latest_consultation.text)

    assert user.email in consultation_page

    confirmation_page = consultation_page.click("Remove")
    consultation_page = confirmation_page.form.submit("confirm_removal").follow()

    assert f"{user.email} has been removed from this consultation" in consultation_page

    assert "There are no users associated with this consultation" in consultation_page

    add_user_page = consultation_page.click("Add users")

    add_user_page.form["users"] = [user.id]
    consultation_page = add_user_page.form.submit().follow()

    assert "Users updated" in consultation_page

    User.objects.exclude(id=user.id).delete()
    add_user_page = consultation_page.click("Add users")

    assert "There are no more users available to add" in add_user_page
