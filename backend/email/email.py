from typing import Any, Mapping

from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_templated_email(
    to: list[str], subject: str, template: str, template_args: Mapping[str, Any]
) -> None:
    body = render_to_string(template, context=template_args, using="jinja2")
    send_mail(subject, body, "this-will-be-discarded@example.com", to)


def send_magic_link_email(to: str, magic_link: str) -> None:
    send_templated_email(
        to=[to],
        subject="Sign in to Consult",
        template="consultations/magic_link_email.md",
        template_args={"magic_link": magic_link},
    )
