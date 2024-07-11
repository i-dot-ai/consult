from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Layout
from django import forms


class TopicModelParametersForm(forms.Form):
    upload_params = forms.FileField(
        label="Upload topic model parameters as a JSON file",
        help_text="Files must be in JSON format",
    )
    # TODO - add validation

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            "upload_params",
            Button("submit", "Upload parameters and generate themes"),
            Button("default_generate_themes", "Generate themes (default parameters) "),
        )
