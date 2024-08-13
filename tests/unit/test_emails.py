from django.core import mail
import pytest

from consultation_analyser.email import send_magic_link_email

@pytest.mark.parametrize("email", [("email@example.com",), ("EMAIL@Example.com",)])
def test_magic_link_email(email):
    send_magic_link_email(
        to=email,
        magic_link="https://example.com",
    )

    sent_mail = mail.outbox[0]
    assert sent_mail.subject == "Sign in to Consult"
    assert [email] == sent_mail.to
    assert "https://example.com" in sent_mail.body

