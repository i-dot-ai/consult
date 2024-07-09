import pytest

from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_user_can_sign_in(django_app):
    UserFactory(email="email@example.com")

    logged_out_homepage = django_app.get("/")
    assert "pilot stage" not in logged_out_homepage

    consultations_index = sign_in(django_app, "email@example.com")

    assert "pilot stage" in consultations_index
