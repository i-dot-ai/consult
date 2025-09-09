import pytest

from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml
from consultation_analyser.consultations.models import Question
from tests.helpers import sign_in


@pytest.mark.xfail(reason="moved to astro")
@pytest.mark.django_db
def test_consultation_page(django_app, dashboard_user):
    consultation = create_dummy_consultation_from_yaml()
    consultation.users.add(dashboard_user)

    sign_in(django_app, dashboard_user.email)

    _question = Question.objects.filter(consultation=consultation).first()
    consultation_page = django_app.get(f"/consultations/{consultation.id}/")

    assert "All Questions" in consultation_page
