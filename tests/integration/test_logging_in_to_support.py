import pytest

from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_logging_in_to_support(client):
    # given I am a logged in admin user
    user = UserFactory(
        email="email@example.com",
        password="admin",  # pragma: allowlist secret
        is_staff=True,
    )
    client.force_login(user)

    # when I visit support
    response = client.get("/support/consultations/")

    # then I should see the support console page
    assert "Consult support console" in response.content.decode()

    # But I shouldn't when I sign out
    response = client.get("/support/sign-out/")
    assert "Consult support console" not in response.content.decode()
