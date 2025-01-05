import pytest

from consultation_analyser.factories2 import UserFactory
from tests.helpers import sign_in
from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml
from consultation_analyser.consultations.models import Question2

@pytest.mark.django_db
def test_consultation_page(django_app):
    user = UserFactory()
    consultation = create_dummy_consultation_from_yaml()
    consultation.users.add(user)

    sign_in(django_app, user.email)

    consultation_slug = consultation.slug
    question = Question2.objects.filter(consultation=consultation).first()
    homepage = django_app.get(f"/consultations/{consultation_slug}/")
    question_page = homepage.click("Question summary")

    assert "Question summary" in question_page
    assert f"{question.text}" in question_page
