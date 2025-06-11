import pytest
from django.contrib.auth.models import Group
from django.urls import reverse

from consultation_analyser import factories
from consultation_analyser.constants import DASHBOARD_ACCESS


@pytest.mark.skip(reason="Doesn't work whilst in the middle of model changes")
@pytest.mark.django_db
def test_dashboard_access(client):
    dash_access = Group.objects.get(name=DASHBOARD_ACCESS)
    user = factories.UserFactory()
    consultation = factories.ConsultationFactory()
    question = factories.QuestionFactory(consultation=consultation)

    dashboard_url_1 = reverse("consultation", args=(consultation.slug,))
    dashboard_url_2 = reverse(
        "question_responses",
        args=(
            consultation.slug,
            question.slug,
        ),
    )

    client.force_login(user)

    # User has consultation access but not dashboard access
    consultation.users.add(user)
    consultation.save()
    response = client.get(dashboard_url_1)
    assert response.status_code == 404
    response = client.get(dashboard_url_2)
    assert response.status_code == 404

    # User has consultation access and dashboard access
    # should be able to see dashboard pages
    user.groups.add(dash_access)
    user.save()
    response = client.get(dashboard_url_1)
    assert response.status_code == 200
    response = client.get(dashboard_url_2)
    assert response.status_code == 200

    # User has dashboard access but not consultation access
    consultation.users.remove(user)
    consultation.save()
    response = client.get(dashboard_url_1)
    assert response.status_code == 404
    response = client.get(dashboard_url_2)
    assert response.status_code == 404
