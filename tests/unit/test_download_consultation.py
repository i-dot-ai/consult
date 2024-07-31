import io
import json

import pytest

from consultation_analyser import factories
from consultation_analyser.consultations import models
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

    consultation_no_themes_json = json.loads(consultation_to_json(consultation))
    assert "themes" not in consultation_no_themes_json.keys()

    consultation_json = json.loads(consultation_to_json(consultation, processing_run=consultation.latest_processing_run))

    assert consultation_json["consultation"]["name"] == "My consultation"

    assert len(consultation_json["consultation"]["sections"]) == 1
    assert len(consultation_json["consultation"]["sections"][0]["questions"]) == 1

    assert len(consultation_json["consultation_responses"]) == 2
    assert len(consultation_json["consultation_responses"][0]["answers"]) == 1

    assert len(consultation_json["themes"]) == 2

    consultation_json["consultation"]["name"] = "My consultation reuploaded"

    reuploadable_without_themes = consultation_json.copy()
    reuploadable_without_themes.pop("themes")
    file_to_reupload = io.BytesIO(json.dumps(reuploadable_without_themes).encode("utf-8"))

    # This will bail if anything goes wrong
    reuploaded = upload_consultation(file_to_reupload, user)

    assert reuploaded





@pytest.mark.django_db
def test_consultation_to_json_processing_runs(django_app):
    # Set up 2 processing runs for a consultation
    consultation = factories.ConsultationWithThemesFactory()
    first_processing_run = models.ProcessingRun.objects.all().order_by("created_at").first()
    second_processing_run = factories.ProcessingRunFactory(consultation=consultation)
    made_up_theme = factories.ThemeFactory(
        processing_run=second_processing_run, short_description="This is my new theme"
    )
    question = models.Question.objects.filter(
        section__consultation=consultation, has_free_text=True
    ).first()
    answer = models.Answer.objects.filter(question=question).first()
    answer.theme = made_up_theme
    answer.save()

    consultation1 = consultation_to_json(consultation, first_processing_run)
    consultation2 = consultation_to_json(consultation, second_processing_run)
    assert consultation1 != consultation2
    assert "This is my new theme" not in consultation1
    assert "This is my new theme" in consultation2
