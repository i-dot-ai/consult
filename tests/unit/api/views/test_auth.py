import jwt
import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_validate_token_pass(client, consultation_user):
    url = reverse("validate-token")
    token = jwt.encode({"email": consultation_user.email}, "secret")
    response = client.post(url, data={"internal_access_token": token})
    assert response.status_code == 200
    assert set(response.json()) == {"access", "sessionId"}


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("data", "status_code", "error"),
    [
        ({}, 400, {"internal_access_token": ["This field is required."]}),
        ({"internal_access_token": "my-token"}, 403, {"detail": "authentication failed"}),
        (
            {"internal_access_token": jwt.encode({"a": "b"}, "secret")},
            403,
            {"detail": "authentication failed"},
        ),
    ],
)
def test_validate_token_fail(client, consultation_user, data, status_code, error):
    url = reverse("validate-token")
    response = client.post(url, data=data)
    assert response.status_code == status_code
    assert response.json() == error
