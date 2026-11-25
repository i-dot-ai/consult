from unittest.mock import patch

import pytest

from consultations.models import Consultation
from data_pipeline.jobs import start_find_themes
from factories import ConsultationFactory


@pytest.mark.django_db
def test_start_find_themes_rolls_stage_back_when_export_fails():
    consultation = ConsultationFactory(stage=Consultation.Stage.FINDING_THEMES)
    with (
        patch(
            "data_pipeline.jobs.export_consultation_inputs_to_s3",
            side_effect=RuntimeError("S3 unavailable"),
        ),
        pytest.raises(RuntimeError, match="S3 unavailable"),
    ):
        start_find_themes(consultation.id, user_id=1)

    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.SETUP


@pytest.mark.django_db
def test_start_find_themes_rolls_stage_back_when_batch_submit_fails():
    consultation = ConsultationFactory(stage=Consultation.Stage.FINDING_THEMES)
    with (
        patch("data_pipeline.jobs.export_consultation_inputs_to_s3", return_value=1),
        patch("data_pipeline.jobs.batch.submit_job", side_effect=RuntimeError("batch down")),
        pytest.raises(RuntimeError, match="batch down"),
    ):
        start_find_themes(consultation.id, user_id=1)

    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.SETUP


@pytest.mark.django_db
def test_start_find_themes_happy_path_returns_code_and_keeps_stage():
    consultation = ConsultationFactory(stage=Consultation.Stage.FINDING_THEMES)
    with (
        patch("data_pipeline.jobs.export_consultation_inputs_to_s3", return_value=1) as export,
        patch("data_pipeline.jobs.batch.submit_job") as submit,
    ):
        result = start_find_themes(consultation.id, user_id=1)

    assert result == consultation.code
    export.assert_called_once_with(consultation, consultation.code)
    submit.assert_called_once()
    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.FINDING_THEMES
