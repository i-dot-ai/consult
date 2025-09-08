import pytest

from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml
from consultation_analyser.consultations.models import Question
from consultation_analyser.factories import UserFactory
from tests.helpers import sign_in


@pytest.mark.xfail(reason="moved to astro")
@pytest.mark.django_db
def test_consultation_page(django_app, dashboard_access_group):
    user = UserFactory()
    consultation = create_dummy_consultation_from_yaml()
    consultation.users.add(user)
    user.groups.add(dashboard_access_group)
    user.save()

    sign_in(django_app, user.email)

    _question = Question.objects.filter(consultation=consultation).first()
    consultation_page = django_app.get(f"/consultations/{consultation.id}/")

    assert "All Questions" in consultation_page
