from django import forms

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Layout


class NewSessionForm(forms.Form):
    email = forms.EmailField(
        label="Email address",
        help_text="Enter the email address you used to register, and we will send you a link to sign in.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {"novalidate": ""}
        self.helper.layout = Layout("email", Button("submit", "Submit"))
