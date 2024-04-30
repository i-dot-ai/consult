import re

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

    assert sign_in_email.subject == "Sign in to Consultation analyser"
    url = re.search("(?P<url>https?://\\S+)", sign_in_email.body).group("url")

    successful_sign_in_page = django_app.get(url)
    homepage = successful_sign_in_page.form.submit().follow().follow()

    mail.outbox.clear()
    return homepage
