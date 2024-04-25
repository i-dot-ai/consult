from django.core import mail

from consultation_analyser.email import send_magic_link_email


def test_magic_link_email():
    send_magic_link_email(
        to="email@example.com",
        magic_link="https://example.com",
    )

    sent_mail = mail.outbox[0]
    assert sent_mail.subject == "Sign in to Consultation analyser"
    assert ["email@example.com"] == sent_mail.to
    assert "https://example.com" in sent_mail.body
