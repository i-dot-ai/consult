import pytest
from django.urls import reverse

from consultation_analyser import factories


@pytest.mark.django_db
def test_dashboard_access(client, dashboard_access_group, consultation, free_text_question):
    user = factories.UserFactory()

    dashboard_url_1 = reverse("consultation", args=(consultation.id,))
    dashboard_url_2 = reverse(
        "question_responses",
        args=(
            consultation.id,
            free_text_question.id,
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
    user.groups.add(dashboard_access_group)
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
