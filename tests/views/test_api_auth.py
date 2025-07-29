from uuid import uuid4

import pytest
from django.urls import reverse
from magic_link.models import MagicLink


@pytest.mark.django_db
def test_token_magic_link(client, user):
    url = reverse("token-magic-link")
    response = client.post(url, data={"email": user.email})
    assert response.status_code == 200
    assert response.json() == {"message":"Magic link sent"}


@pytest.mark.django_db
def test_token_magic_link_fail(client, user):
    url = reverse("token-magic-link")
    response = client.post(url, data={"user": user.email})
    assert response.status_code == 400
    assert response.json() == {"detail":"Email required"}


@pytest.mark.django_db
def test_create_token(client, user):
    link = MagicLink.objects.create(user=user)
    url = reverse("create-token", kwargs={"token": link.token})
    response = client.get(url)
    assert response.status_code == 200
    assert "access" in response.json()
    assert "refresh" in response.json()


@pytest.mark.django_db
def test_create_token_fail(client, user):
    token = uuid4()
    url = reverse("create-token", kwargs={"token": token})
    response = client.get(url)
    assert response.status_code == 404
    assert response.json() == {"detail":"No MagicLink matches the given query."}

