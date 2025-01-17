from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Field, Layout, Size
from django import forms


class AddUsersToConsultationForm(forms.Form):
    users = forms.MultipleChoiceField(
        choices=[],
        widget=forms.CheckboxSelectMultiple,
        label="Add users",
        error_messages={"required": "Please select at least one user to add"},
    )

    def __init__(self, *args, **kwargs):
        users = kwargs.pop("users")
        consultation = kwargs.pop("consultation")

        super().__init__(*args, **kwargs)

        self.consultation = consultation
        self.has_users = len(users) > 0

        self.fields["users"].choices = [(u.id, u.email) for u in users]
        self.fields["users"].help_text = f"Adding to {consultation.title}"
        self.helper = FormHelper()
        if self.has_users:
            self.helper.layout = Layout(
                Field.checkboxes("users", legend_size=Size.LARGE),
                Button("submit", "Save and continue"),
            )
        else:
            self.helper.layout = Layout(
                Field.checkboxes("users", legend_size=Size.LARGE),
            )
