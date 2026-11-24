from unittest.mock import patch

import pytest

from consultations.models import Consultation
from data_pipeline.jobs import (
    complete_find_themes,
    find_themes,
    import_candidate_themes,
    reset_find_themes_after_worker_failure,
)


@pytest.mark.django_db
def test_find_themes_job_runs_pipeline_and_starts_candidate_mapping(consultation):
    consultation.stage = Consultation.Stage.FINDING_THEMES
    consultation.running_job = Consultation.RunningJob.FIND_THEMES
    consultation.save(update_fields=["stage", "running_job"])

    with (
        patch("data_pipeline.find_themes.find_themes", return_value="2026-11-23") as run,
        patch("data_pipeline.sync.consultation_inputs.export_consultation_inputs_to_s3") as export,
        patch("data_pipeline.sync.candidate_themes.import_candidate_themes_from_s3") as import_,
        patch("data_pipeline.sync.candidate_themes.export_candidate_themes_to_s3") as export_themes,
        patch("data_pipeline.batch.submit_job") as submit,
        patch("data_pipeline.events.publish_find_themes_event") as publish,
    ):
        find_themes(consultation.id, 123)

    export.assert_called_once()
    run.assert_called_once_with(consultation.code, consultation.model_name)
    import_.assert_called_once_with(consultation.code, "2026-11-23")
    export_themes.assert_called_once()
    assert submit.call_args.kwargs["assignment_target"] == "candidate_themes"
    assert [call.kwargs["status"] for call in publish.call_args_list] == ["RUNNING", "SUCCEEDED"]
    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.FINALISING_THEMES
    assert consultation.running_job is None


@pytest.mark.django_db
def test_mapping_submission_failure_does_not_discard_discovered_themes(consultation):
    consultation.stage = Consultation.Stage.FINDING_THEMES
    consultation.running_job = Consultation.RunningJob.FIND_THEMES
    consultation.save(update_fields=["stage", "running_job"])

    with (
        patch("data_pipeline.find_themes.find_themes", return_value="2026-11-23"),
        patch("data_pipeline.sync.consultation_inputs.export_consultation_inputs_to_s3"),
        patch("data_pipeline.sync.candidate_themes.import_candidate_themes_from_s3"),
        patch("data_pipeline.sync.candidate_themes.export_candidate_themes_to_s3"),
        patch("data_pipeline.batch.submit_job", side_effect=RuntimeError("Batch unavailable")),
        patch("data_pipeline.events.publish_find_themes_event"),
        pytest.raises(RuntimeError, match="Batch unavailable"),
    ):
        find_themes(consultation.id, 123)

    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.FINALISING_THEMES
    assert consultation.running_job is None


@pytest.mark.django_db
def test_find_themes_job_is_retryable_after_failure(consultation):
    consultation.stage = Consultation.Stage.FINDING_THEMES
    consultation.running_job = Consultation.RunningJob.FIND_THEMES
    consultation.save(update_fields=["stage", "running_job"])

    with (
        patch(
            "data_pipeline.sync.consultation_inputs.export_consultation_inputs_to_s3",
            side_effect=RuntimeError("S3 unavailable"),
        ),
        patch("data_pipeline.events.publish_find_themes_event") as publish,
        pytest.raises(RuntimeError, match="S3 unavailable"),
    ):
        find_themes(consultation.id, 123)

    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.SETUP
    assert consultation.running_job is None
    assert [call.kwargs["status"] for call in publish.call_args_list] == ["RUNNING", "FAILED"]


@pytest.mark.django_db
def test_rq_failure_callback_recovers_stuck_consultation(consultation):
    consultation.stage = Consultation.Stage.FINDING_THEMES
    consultation.running_job = Consultation.RunningJob.FIND_THEMES
    consultation.save(update_fields=["stage", "running_job"])
    rq_job = type("Job", (), {"args": [consultation.id]})()

    reset_find_themes_after_worker_failure(rq_job, None, RuntimeError, RuntimeError(), None)

    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.SETUP
    assert consultation.running_job is None


@pytest.mark.django_db
def test_complete_find_themes_owns_import_and_mapping(consultation):
    consultation.stage = Consultation.Stage.FINDING_THEMES
    consultation.running_job = Consultation.RunningJob.FIND_THEMES
    consultation.save(update_fields=["stage", "running_job"])

    with (
        patch("data_pipeline.sync.candidate_themes.import_candidate_themes_from_s3") as import_,
        patch("data_pipeline.sync.candidate_themes.export_candidate_themes_to_s3") as export,
        patch("data_pipeline.batch.submit_job") as submit,
    ):
        complete_find_themes(
            consultation_code=consultation.code,
            run_date="2026-11-23",
            user_id=123,
            model_name="gpt-4.1",
        )

    import_.assert_called_once_with(consultation.code, "2026-11-23")
    export.assert_called_once()
    assert submit.call_args.kwargs["assignment_target"] == "candidate_themes"
    consultation.refresh_from_db()
    assert consultation.stage == Consultation.Stage.FINALISING_THEMES
    assert consultation.running_job is None


def test_import_candidate_themes_job_is_only_a_recovery_wrapper():
    with patch("data_pipeline.jobs.complete_find_themes") as complete:
        import_candidate_themes("consultation-code", "2026-11-23", "123", "gpt-4.1")

    complete.assert_called_once_with(
        consultation_code="consultation-code",
        run_date="2026-11-23",
        user_id="123",
        model_name="gpt-4.1",
    )
