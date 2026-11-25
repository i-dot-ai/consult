"""
RQ job wrappers for data pipeline operations.

These functions are designed to be executed asynchronously via RQ (Redis Queue).
"""

from uuid import UUID

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings

from consultations.models import Consultation
from data_pipeline import batch
from data_pipeline.sync.consultation_inputs import export_consultation_inputs_to_s3
from rq_context import job

logger = settings.LOGGER


@job("default", timeout=900)  # 15 minutes
def start_find_themes(
    consultation_id: UUID,
    user_id: int,
) -> str:
    """Export consultation inputs to S3 and submit the find-themes Batch job."""
    # user_id is passed through into Batch metadata for auditability, even if the user is deleted later.
    try:
        consultation = Consultation.objects.get(pk=consultation_id)
    except Consultation.DoesNotExist:
        logger.info(
            "Consultation {consultation_id} no longer exists; skipping find-themes",
            consultation_id=consultation_id,
        )
        return ""

    if consultation.stage != Consultation.Stage.FINDING_THEMES:
        logger.warning(
            "Consultation {consultation_id} not in FINDING_THEMES; skipping find-themes",
            consultation_id=consultation_id,
            stage=consultation.stage,
        )
        return ""
    logger.set_context_field("consultation_id", str(consultation.id))

    consultation_code = consultation.code

    def _rollback_stage(reason: str) -> None:
        rerolled = Consultation.objects.filter(
            pk=consultation.pk, stage=Consultation.Stage.FINDING_THEMES
        ).update(stage=Consultation.Stage.SETUP)
        if not rerolled:
            logger.error(
                "Stage rollback skipped after {reason} for consultation '{consultation_id}' "
                "(stage already changed)",
                reason=reason,
                consultation_id=consultation.id,
            )

    try:
        question_parts = export_consultation_inputs_to_s3(consultation, consultation_code)
        logger.info(
            "Mirrored {question_parts} question parts to s3 for consultation '{consultation_code}' "
            "before find-themes kickoff",
            question_parts=question_parts,
            consultation_code=consultation_code,
        )

        batch.submit_job(
            job_type="FIND_THEMES",
            consultation_code=consultation_code,
            consultation_name=consultation.title,
            user_id=user_id,
            model_name=consultation.model_name,
        )
    except (ClientError, BotoCoreError):
        _rollback_stage("AWS call failure")
        raise
    except Exception:
        _rollback_stage("unexpected error")
        raise

    logger.info(
        "Find Themes job submitted for consultation {consultation_id} by user {user_id}",
        consultation_id=consultation.id,
        user_id=user_id,
    )

    return consultation_code


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
    """Import candidate themes from S3, then start assign-themes for candidate theme responses."""
    from consultations.models import Consultation
    from data_pipeline import batch
    from data_pipeline.sync.candidate_themes import (
        export_candidate_themes_to_s3,
        import_candidate_themes_from_s3,
    )

    try:
        import_candidate_themes_from_s3(
            consultation_code=consultation_code,
            timestamp=run_date,
        )
    except Exception:
        logger.exception(
            "import_candidate_themes_from_s3 failed for consultation_code={consultation_code}, "
            "run_date={run_date}",
            consultation_code=consultation_code,
            run_date=run_date,
        )
        raise

    # After importing candidate themes, automatically start assign-themes
    # so users can review assigned responses during theme finalisation.
    try:
        consultation = Consultation.objects.get(code=consultation_code)
    except Exception:
        logger.exception(
            "Failed to fetch consultation for consultation_code={consultation_code} "
            "after importing candidate themes",
            consultation_code=consultation_code,
        )
        raise

    try:
        consultation.stage = Consultation.Stage.FINALISING_THEMES
        consultation.save(update_fields=["stage"])
    except Exception:
        logger.exception(
            "Failed to update consultation stage for consultation_code={consultation_code} "
            "after importing candidate themes",
            consultation_code=consultation_code,
        )
        # Do not raise if fails as this is not a crucial step

    try:
        export_candidate_themes_to_s3(consultation)
    except Exception:
        logger.exception(
            "export_candidate_themes_to_s3 failed for consultation_code={consultation_code}",
            consultation_code=consultation_code,
        )
        raise

    batch.submit_job(
        job_type="ASSIGN_THEMES",
        consultation_code=consultation.code,
        consultation_name=consultation.title,
        user_id=int(user_id) if user_id else consultation.created_by_id,
        model_name=model_name or consultation.model_name,
        assignment_target="candidate_themes",
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
