import io
import json

import pytest
from django.conf import settings

from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.factories import UserFactory


@pytest.mark.django_db
def test_consultation_to_json(django_app):
    user = UserFactory()
    file = open(settings.BASE_DIR / "tests" / "examples" / "upload.json", "rb")

    consultation = upload_consultation(file, user)

    consultation_json = json.loads(consultation_to_json(consultation))

    assert consultation_json["consultation"]["name"] == "My consultation"

    assert len(consultation_json["consultation"]["sections"]) == 1
    assert len(consultation_json["consultation"]["sections"][0]["questions"]) == 3

    assert len(consultation_json["consultation_responses"]) == 2
    assert len(consultation_json["consultation_responses"][0]["answers"]) == 3

    consultation_json["consultation"]["name"] = "My consultation reuploaded"

    file_to_reupload = io.StringIO(json.dumps(consultation_json))

    # This will bail if anything goes wrong
    reuploaded = upload_consultation(file_to_reupload, user)

    assert reuploaded
