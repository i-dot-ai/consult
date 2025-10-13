import os
import time
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


def sign_in(django_app, email):
    user = User.objects.get(email=email)

    # Generate JWT token (simulating OAuth success view)
    access_token = AccessToken.for_user(user)

    # Mock the OAuth redirect and cookie setting
    # Instead of going through OAuth flow, we'll directly set cookies
    _homepage = django_app.get("/")

    # Set authentication cookies (simulating Django OAuth success view)
    django_app.set_cookie("access", str(access_token))
    django_app.set_cookie("sessionId", "test-session-id")

    # Also set Authorization header for JWT middleware
    django_app.authorization = ("Bearer", str(access_token))

    # Get homepage again with authentication cookies
    authenticated_homepage = django_app.get("/")

    return authenticated_homepage


def save_and_open_page(html_string) -> None:
    """
    Given page content from webtest, write it to /tmp
    and pop it open in the browser
    """

    dir = settings.BASE_DIR / "tmp" / "integration-test-html-snapshots"
    Path(dir).mkdir(parents=True, exist_ok=True)

    filename = dir / f"test-html-{int(time.time())}.html"

    with open(filename, "wb") as f:
        f.write(html_string)

    os.system(f"open {filename}")  # nosec
