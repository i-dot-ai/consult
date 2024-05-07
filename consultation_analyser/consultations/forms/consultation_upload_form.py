import json

from crispy_forms_gds.helper import FormHelper
from crispy_forms_gds.layout import Button, Layout
from django import forms
from django.core import exceptions as django_exceptions
from jsonschema import exceptions as jsonschema_exceptions
from jsonschema import validate
from jsonschema.validators import Draft202012Validator

from consultation_analyser.consultations.views.schema import SCHEMA_DIR  # refactor this


def validate_consultation_json(value):
    uploaded_json = json.loads(value.read())
    with open(f"{SCHEMA_DIR}/consultation_with_responses_schema.json") as f:
        schema = json.loads(f.read())

    try:
        validate(uploaded_json, schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    except jsonschema_exceptions.ValidationError as e:
        path = [str(el) for el in e.path]
        raise django_exceptions.ValidationError(f"{' > '.join(path)} > {e.message}")
    finally:
        # rewind the file for the next caller
        value.seek(0)


class ConsultationUploadForm(forms.Form):
    consultation_json = forms.FileField(
        validators=[validate_consultation_json],
        label="Upload a consultation file",
        help_text="Files must be in JSON format to match the <a class='govuk-link' href='/schema'>required schema</a>",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout("consultation_json", Button("submit", "Upload consultation"))
