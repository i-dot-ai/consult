from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Field, Layout, Submit
from django import forms

from consultation_analyser.authentication.models import User


class EditUserForm(forms.Form):
    is_staff = forms.BooleanField(
        label="Can access support console",
        required=False,
    )

    user_id = forms.IntegerField()

    def clean(self):
        cleaned_data = super().clean()
        user_id = cleaned_data.get("user_id")

        if (self.current_user.id == user_id) and cleaned_data["is_staff"] is not True:
            raise forms.ValidationError("You cannot remove admin privileges from your own user")

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field("user_id", type="hidden"),
            Field.checkboxes("is_staff"),
            Submit("submit", "Update user"),
        )
