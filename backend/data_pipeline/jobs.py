"""
RQ job wrappers for data pipeline operations.

These functions are designed to be executed asynchronously via RQ (Redis Queue).
"""

from uuid import UUID

from django.conf import settings

from rq_context import job

logger = settings.LOGGER

DEFAULT_TIMEOUT_SECONDS = 3_600


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
