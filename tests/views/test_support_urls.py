import pytest
from django.urls import reverse

from consultation_analyser import factories_old


@pytest.mark.django_db
def test_support_url_access(client):
    url = reverse("users")
    # Check anonymous user
    response = client.get(url)
    assert response.status_code == 404

    # Check normal non-staff user can't access
    user = factories_old.UserFactory()
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 404

    # Check staff user can access
    user = factories_old.UserFactory(is_staff=True)
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
