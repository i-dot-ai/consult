from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Layout
from django import forms
from django.core.exceptions import ValidationError

from consultation_analyser.authentication.models import User


def validate_unique_email(value):
    if User.objects.filter(email=value).exists():
        raise ValidationError("A user already exists with this email address")


class NewUserForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        help_text="Enter the email of the user to invite",
        error_messages={
            "required": "Your email address is required",
            "invalid": "Enter a valid email address",
        },
        validators=[validate_unique_email],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout("email", Button("submit", "Continue"))
