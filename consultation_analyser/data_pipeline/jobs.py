"""
RQ job wrappers for data pipeline operations.

These functions are designed to be executed asynchronously via RQ (Redis Queue).
"""

from uuid import UUID

from django.conf import settings
from django_rq import job

logger = settings.LOGGER

DEFAULT_TIMEOUT_SECONDS = 3_600


@job("default", timeout=3600)
def import_consultation_job(
    consultation_name: str,
    consultation_code: str,
    user_id: UUID,
) -> UUID:
    """Import consultation setup data from S3."""
    from consultation_analyser.data_pipeline.sync.consultation_setup import (
        import_consultation_from_s3,
    )

    logger.refresh_context()

    return import_consultation_from_s3(
        consultation_code=consultation_code,
        consultation_title=consultation_name,
        user_id=user_id,
        enqueue_embeddings=True,
    )


@job("default", timeout=3600)
def import_candidate_themes_job(
    consultation_code: str,
    run_date: str,
) -> None:
    """Import candidate themes from S3 (find-themes batch job output)."""
    from consultation_analyser.data_pipeline.sync.candidate_themes import (
        import_candidate_themes_from_s3,
    )

    logger.refresh_context()

    import_candidate_themes_from_s3(
        consultation_code=consultation_code,
        timestamp=run_date,
    )


@job("default", timeout=3600)
def import_response_annotations_job(
    consultation_code: str,
    run_date: str,
) -> None:
    """Import response annotations from S3 (assign-themes batch job output)."""
    from consultation_analyser.data_pipeline.sync.response_annotations import (
        import_response_annotations_from_s3,
    )

    logger.refresh_context()

    import_response_annotations_from_s3(
        consultation_code=consultation_code,
        timestamp=run_date,
    )
