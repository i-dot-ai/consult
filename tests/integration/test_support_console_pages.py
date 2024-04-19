import pytest

from consultation_analyser.consultations.dummy_data import DummyConsultation
from consultation_analyser.consultations.models import Consultation, Theme
from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_logging_in_to_support(django_app):
    # given I am an admin user
    UserFactory(email="email@example.com", password="admin", is_staff=True)  # pragma: allowlist secret

    # when I visit support
    login_page = django_app.get("/support").follow().follow()  # 2 redirects

    # and I sign in to support
    login_page.form["username"] = "email@example.com"  # Django field is called "username"
    login_page.form["password"] = "admin"  # pragma: allowlist secret
    support_home = login_page.form.submit().follow()

    # then I should see the support console page
    assert "Consultation analyser support console" in support_home

    logged_out_page = support_home.click("Sign out")

    assert "Consultation analyser support console" not in logged_out_page


@pytest.mark.django_db
def test_generating_dummy_data(django_app):
    page_url = "/support/consultations/"
    UserFactory(email="email@example.com", password="admin", is_staff=True)  # pragma: allowlist secret
    login_page = django_app.get(page_url).follow()
    login_page.form["username"] = "email@example.com"
    login_page.form["password"] = "admin"  # pragma: allowlist secret
    consultations_page = login_page.form.submit().follow()
    assert "All consultations" in consultations_page

    # Check dummy data button does generate a new consultation
    initial_count = Consultation.objects.all().count()
    consultations_page = consultations_page.form.submit("generate_dummy_consultation")
    count_after_dummy_data = Consultation.objects.all().count()
    assert count_after_dummy_data > initial_count

    # Check redirected to individual consultation page in support
    latest_consultation = Consultation.objects.all().order_by("created_at").last()
    next_page = consultations_page.click(latest_consultation.name)
    assert "Generate themes" in next_page


@pytest.mark.django_db
def test_generate_themes(django_app):
    DummyConsultation(name="Test consultation", slug="test-consultation", include_themes=False)
    UserFactory(email="email@example.com", password="admin", is_staff=True)  # pragma: allowlist secret
    login_page = django_app.get("/support/consultations/test-consultation/").follow()
    login_page.form["username"] = "email@example.com"
    login_page.form["password"] = "admin"  # pragma: allowlist secret
    consultation_page = login_page.form.submit().follow()
    assert "Test consultation" in consultation_page
    consultation_page = consultation_page.form.submit("generate_themes")
    generated_themes = Theme.objects.filter(answer__question__section__consultation__slug="test-consultation")
    assert generated_themes.exists()
