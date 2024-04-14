import pytest

from tests.factories import UserFactory


@pytest.mark.django_db
def test_logging_in_to_support(django_app):
    # given I am an admin user
    UserFactory(email="email@example.com", password="admin", is_staff=True)

    # when I visit support
    form = django_app.get("/support").follow().form

    # and I sign in to support
    form["email"] = "email@example.com"
    form["password"] = "admin"
    response = form.submit().follow()

    # then I should see the support console page
    assert "Consultation support console" in response
