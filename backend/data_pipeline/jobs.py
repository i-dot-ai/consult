"""
RQ job wrappers for data pipeline operations.

These functions are designed to be executed asynchronously via RQ (Redis Queue).
"""

from typing import Literal
from uuid import UUID

from django.conf import settings
from django.db import transaction
from rq import get_current_job

from logging_context import get_or_create_context_id
from rq_context import job

logger = settings.LOGGER

DEFAULT_TIMEOUT_SECONDS = 3_600


def reset_find_themes_after_worker_failure(rq_job, connection, exception_type, value, traceback):
    """Recover state when RQ terminates the job before its own cleanup can run."""
    from consultations.models import Consultation

    consultation_id = rq_job.args[0]
    Consultation.objects.filter(id=consultation_id, stage=Consultation.Stage.FINDING_THEMES).update(
        stage=Consultation.Stage.SETUP, running_job=None
    )


def complete_find_themes(
    consultation_code: str,
    run_date: str,
    user_id: int | str | None = None,
    model_name: str | None = None,
) -> None:
    """Import discovered themes and start mapping without enqueueing another worker job."""
    from consultations.models import Consultation
    from data_pipeline import batch
    from data_pipeline.sync.candidate_themes import (
        export_candidate_themes_to_s3,
        import_candidate_themes_from_s3,
    )

    import_candidate_themes_from_s3(consultation_code, run_date)
    consultation = Consultation.objects.get(code=consultation_code)
    export_candidate_themes_to_s3(consultation)

    # Discovery is durable before the separately managed mapping job is submitted.
    consultation.stage = Consultation.Stage.FINALISING_THEMES
    consultation.running_job = None
    consultation.save(update_fields=["stage", "running_job"])

    resolved_user_id = int(user_id) if user_id is not None else consultation.created_by_id
    if resolved_user_id is None:
        raise ValueError(
            f"No user available to start candidate-theme mapping for '{consultation_code}'"
        )
    resolved_model_name = model_name or consultation.model_name or Consultation.ModelName.GPT_41
    batch.submit_job(
        job_type="ASSIGN_THEMES",
        consultation_code=consultation.code,
        consultation_name=consultation.title,
        user_id=resolved_user_id,
        model_name=resolved_model_name,
        assignment_target="candidate_themes",
    )


@job(
    "default",
    timeout=86400,
    on_failure=reset_find_themes_after_worker_failure,
)  # Theme discovery can run for several hours.
def find_themes(consultation_id: UUID, user_id: int) -> None:
    """Run theme discovery, persist its results, then start candidate-theme mapping."""
    from consultations.models import Consultation
    from data_pipeline.events import publish_find_themes_event
    from data_pipeline.find_themes import find_themes as run_find_themes
    from data_pipeline.sync.consultation_inputs import (
        assign_consultation_code,
        export_consultation_inputs_to_s3,
        sync_has_free_text_with_type,
    )

    context_id = get_or_create_context_id()
    rq_job = get_current_job()
    job_id = rq_job.id if rq_job else None
    consultation = None
    consultation_code = "unknown"

    def publish(status: Literal["RUNNING", "SUCCEEDED", "FAILED"]) -> None:
        if consultation is None:
            return
        publish_find_themes_event(
            status=status,
            consultation_code=consultation_code,
            consultation_name=consultation.title,
            user_id=user_id,
            job_id=job_id,
            context_id=context_id,
        )

    try:
        consultation = Consultation.objects.get(id=consultation_id)
        consultation_code = assign_consultation_code(consultation)
        model_name = consultation.model_name or Consultation.ModelName.GPT_41
        publish("RUNNING")
        if consultation.stage != Consultation.Stage.FINDING_THEMES:
            raise ValueError(f"Consultation '{consultation.id}' is not in the finding themes stage")
        sync_has_free_text_with_type(consultation)
        export_consultation_inputs_to_s3(consultation, consultation_code)
        run_date = run_find_themes(consultation_code, model_name)
        complete_find_themes(
            consultation_code=consultation_code,
            run_date=run_date,
            user_id=user_id,
            model_name=model_name,
        )
        publish("SUCCEEDED")
    except Exception:
        logger.exception(
            "Find-themes worker job failed for consultation_id={consultation_id}",
            consultation_id=consultation_id,
        )
        # Returning to setup gives users an explicit retry path after a failed worker job.
        with transaction.atomic():
            Consultation.objects.filter(
                id=consultation_id, stage=Consultation.Stage.FINDING_THEMES
            ).update(stage=Consultation.Stage.SETUP, running_job=None)
        publish("FAILED")
        raise


@job("default", timeout=86400)  # 1 day
def import_consultation(
    consultation_name: str,
    consultation_code: str,
    user_id: UUID,
) -> UUID:
    """Import consultation setup data from S3."""
    from data_pipeline.sync.consultation_setup import (
        import_consultation_from_s3,
    )

    try:
        return import_consultation_from_s3(
            consultation_code=consultation_code,
            consultation_title=consultation_name,
            user_id=user_id,
        )
    except Exception:
        logger.exception(
            "import_consultation job failed for consultation_code={consultation_code} "
            "(consultation_name={consultation_name}, user_id={user_id})",
            consultation_code=consultation_code,
            consultation_name=consultation_name,
            user_id=user_id,
        )
        raise


@job("default", timeout=3600)
def import_candidate_themes(
    consultation_code: str,
    run_date: str,
    user_id: str | None = None,
    model_name: str | None = None,
) -> None:
    """Admin recovery wrapper for completing an existing S3 find-themes run."""
    complete_find_themes(
        consultation_code=consultation_code,
        run_date=run_date,
        user_id=user_id,
        model_name=model_name,
    )


@job("default", timeout=14400)
def import_response_annotations(
    consultation_code: str,
    run_date: str,
) -> None:
    """Import response annotations from S3 (assign-themes batch job output)."""
    from consultations.models import Consultation
    from data_pipeline.sync.response_annotations import (
        import_response_annotations_from_s3,
    )

    try:
        import_response_annotations_from_s3(
            consultation_code=consultation_code,
            timestamp=run_date,
        )
    except Exception:
        logger.exception(
            "import_response_annotations job failed for consultation_code={consultation_code}, "
            "run_date={run_date}",
            consultation_code=consultation_code,
            run_date=run_date,
        )
        raise
    finally:
        try:
            consultation = Consultation.objects.get(code=consultation_code)
            consultation.running_job = None
            consultation.save(update_fields=["running_job"])
        except Exception:
            logger.exception(
                "Failed to update running_job value for consultation_code={consultation_code} "
                "while importing response annotations",
                consultation_code=consultation_code,
            )


@job("default", timeout=3600)
def import_candidate_theme_responses(
    consultation_code: str,
    run_date: str,
) -> None:
    """Import candidate theme response mappings from S3 (assign-themes batch job output during finalising)."""
    from data_pipeline.sync.candidate_themes import (
        import_candidate_theme_responses_from_s3,
    )

    try:
        import_candidate_theme_responses_from_s3(
            consultation_code=consultation_code,
            timestamp=run_date,
        )
    except Exception:
        logger.exception(
            "import_candidate_theme_responses job failed for consultation_code={consultation_code}, "
            "run_date={run_date}",
            consultation_code=consultation_code,
            run_date=run_date,
        )
        raise
