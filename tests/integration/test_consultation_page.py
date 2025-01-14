import pytest

from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml
from consultation_analyser.consultations.models import Question
from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_consultation_page(django_app):
    user = UserFactory()
    consultation = create_dummy_consultation_from_yaml()
    consultation.users.add(user)

    sign_in(django_app, user.email)

    consultation_slug = consultation.slug
    question = Question.objects.filter(consultation=consultation).first()
    consultation_page = django_app.get(f"/consultations/{consultation_slug}/")
    question_page = consultation_page.click("Question summary", index=0)

    assert "Question summary" in question_page
    assert f"{question.text}" in question_page
