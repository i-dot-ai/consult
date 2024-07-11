import os
import re
import time
from pathlib import Path

from django.conf import settings
from django.core import mail


def sign_in(django_app, email):
    homepage = django_app.get("/")
    homepage.click("Sign in", index=0)

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = "invalid@example.com"
    login_page.form.submit()

    login_page = django_app.get("/sign-in/")
    login_page.form["email"] = email
    login_page.form.submit()

    sign_in_email = mail.outbox[0]

    assert sign_in_email.subject == "Sign in to Consult"
    url = re.search("(?P<url>https?://\\S+)", sign_in_email.body).group("url")

    successful_sign_in_page = django_app.get(url)
    homepage = successful_sign_in_page.form.submit().follow().follow()

    mail.outbox.clear()
    return homepage


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
