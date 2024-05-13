import json

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from consultation_analyser.consultations.forms.consultation_upload_form import ConsultationUploadForm
from consultation_analyser.consultations.public_schema import Question, Section


def test_consultation_upload_form_is_valid_for_example_json():
    file_path = settings.BASE_DIR / "tests" / "examples" / "upload.json"
    with open(file_path, "rb") as f:
        uploaded_file = SimpleUploadedFile(file_path.name, f.read(), content_type="application/json")

    form = ConsultationUploadForm({}, {"consultation_json": uploaded_file})

    assert form.is_valid()


def test_consultation_upload_form_is_invalid_with_clashing_section_names():
    file_path = settings.BASE_DIR / "tests" / "examples" / "upload.json"
    with open(file_path, "rb") as f:
        contents = json.loads(f.read())
        question = Question(id="question-99", text="Why?", has_free_text=True)
        contents["consultation"]["sections"] += [
            Section(name="Duplicated section", questions=[question]).model_dump(),
            Section(name="Duplicated section", questions=[question]).model_dump(),
        ]

        json_to_upload = json.dumps(contents)

        uploaded_file = SimpleUploadedFile(file_path.name, str.encode(json_to_upload), content_type="application/json")

    form = ConsultationUploadForm({}, {"consultation_json": uploaded_file})

    assert not form.is_valid()
    assert form.errors["consultation_json"] == ["Duplicate sections: Duplicated section"]
