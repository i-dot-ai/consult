import pytest

from consultation_analyser.factories import ConsultationFactory


@pytest.mark.django_db
def test_logged_out_user_sees_404s(django_app):
    ConsultationFactory(slug="whatever")

    returned_page = django_app.get("/consultations/whatever/", expect_errors=True)

    assert "Page not found" in returned_page
