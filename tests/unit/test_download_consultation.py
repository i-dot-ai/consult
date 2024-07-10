import io
import json

import pytest

from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.factories import ConsultationBuilder, UserFactory


@pytest.mark.django_db
def test_consultation_to_json(django_app):
    user = UserFactory()

    consultation_builder = ConsultationBuilder(name="My consultation")
    consultation = consultation_builder.consultation
    question = consultation_builder.add_question()

    answer = consultation_builder.add_answer(question)
    consultation_builder.add_theme(answer)
    consultation_builder.next_response()
    answer = consultation_builder.add_answer(question)
    consultation_builder.add_theme(answer)

    consultation_json = json.loads(consultation_to_json(consultation))

    assert consultation_json["consultation"]["name"] == "My consultation"

    assert len(consultation_json["consultation"]["sections"]) == 1
    assert len(consultation_json["consultation"]["sections"][0]["questions"]) == 1

    assert len(consultation_json["consultation_responses"]) == 2
    assert len(consultation_json["consultation_responses"][0]["answers"]) == 1

    assert len(consultation_json["themes"]) == 2

    consultation_json["consultation"]["name"] = "My consultation reuploaded"

    reuploadable_without_themes = consultation_json.copy()
    reuploadable_without_themes.pop("themes")
    file_to_reupload = io.BytesIO(json.dumps(reuploadable_without_themes).encode('utf-8'))

    # This will bail if anything goes wrong
    reuploaded = upload_consultation(file_to_reupload, user)

    assert reuploaded
