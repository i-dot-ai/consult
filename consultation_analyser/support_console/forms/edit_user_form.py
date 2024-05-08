from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Submit, Layout
from django import forms

from consultation_analyser.authentication.models import User


class EditUserForm(forms.Form):
    is_staff = forms.BooleanField(
        label="Can access support console",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field.checkboxes("is_staff"),
            Submit("submit", "Update user"),
        )
