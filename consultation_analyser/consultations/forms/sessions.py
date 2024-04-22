from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Layout
from django import forms


class NewSessionForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        help_text="Enter your email address to generate a link to sign in",
        error_messages={"required": "Your email address is required", "invalid": "Enter a valid email address"},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout("email", Button("submit", "Continue"))
