from django.test import override_settings
from django.urls import reverse


@override_settings(GIT_SHA="00000000-0000-0000-0000-000000000000")
def test_git_sha(client):
    url = reverse("git-sha")

    response = client.get(url)
    assert response.status_code == 200
    assert response.json() == {"sha": "00000000-0000-0000-0000-000000000000"}
