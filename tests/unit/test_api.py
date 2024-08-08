import json

import pytest
from django.conf import settings
from ninja_jwt.tokens import RefreshToken

from consultation_analyser import factories

UPLOAD_CONSULTATION_URL = "/support/api/upload-consultation/"
VALID_CONSULTATION_UPLOAD = settings.BASE_DIR / "tests" / "examples" / "chocolate.json"


@pytest.mark.django_db
def test_upload_consultation_no_auth(client):
	response = client.post(UPLOAD_CONSULTATION_URL)
	assert response.status_code == 401


@pytest.mark.django_db
def test_upload_consultation_valid(client):
    user = factories.UserFactory(email="staff@example.com", is_staff=True)
    client.force_login(user)
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    headers = {"Authorization": f"Bearer {access_token}"}
    with open(VALID_CONSULTATION_UPLOAD, "r") as file:
        data = json.load(file)

    response = client.post(UPLOAD_CONSULTATION_URL, headers=headers, data=json.dumps(data), content_type="application/json")
    assert response.status_code == 200

