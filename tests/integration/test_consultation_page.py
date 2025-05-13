import pytest
from django.contrib.auth.models import Group

from consultation_analyser.constants import DASHBOARD_ACCESS
from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml
from consultation_analyser.consultations.models import Question
from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.django_db
def test_consultation_page(django_app):
    user = UserFactory()
    consultation = create_dummy_consultation_from_yaml()
    consultation.users.add(user)
    dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user.groups.add(dash_access)
    user.save()

    sign_in(django_app, user.email)

    consultation_slug = consultation.slug
    question = Question.objects.filter(consultation=consultation).first()
    consultation_page = django_app.get(f"/consultations/{consultation_slug}/")

    assert "All Questions" in consultation_page
    assert "Free text response" in consultation_page
    assert question.text in consultation_page

    response_page = consultation_page.click("Question 1", index=0)
    assert f"{question.text}" in response_page
