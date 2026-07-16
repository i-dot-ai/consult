import os

import redis  # type: ignore
import sentry_sdk
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import (
    ContextEnrichmentType,
    ExecutionEnvironmentType,
)
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat
from rq import Queue

logger = StructuredLogger(
    level="info",
    options={
        "execution_environment": ExecutionEnvironmentType.LAMBDA,
        "log_format": LogOutputFormat.JSON,
    },
)
# Initialize Sentry if DSN is provided
sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=os.environ.get("ENVIRONMENT", "unknown"),
        traces_sample_rate=1.0,
    )
    logger.info("Sentry initialized")


def lambda_handler(event, context):
    """
    Lambda triggered by EventBridge when assign themes batch job completes.

    Enqueues a Django RQ job to import response annotations from S3 to the database.
    """
    logger.refresh_context([{"type": ContextEnrichmentType.LAMBDA, "object": context}])

    detail = event["detail"]
    job_name = detail["jobName"]
    job_status = detail["status"]

    parameters = detail["parameters"]
    consultation_code = parameters["consultation_code"]
    run_date = parameters["run_date"]
    assignment_target = parameters.get("assignment_target", "selected_themes")

    logger.set_context_field("batch_job_name", job_name)
    logger.set_context_field("consultation_code", consultation_code)

    logger.info(
        "Batch job '{job_name}' completed with status: {job_status} "
        "consultation_code: {consultation_code} date: {run_date} assignment_target: {assignment_target}",
        job_name=job_name,
        job_status=job_status,
        consultation_code=consultation_code,
        run_date=run_date,
        assignment_target=assignment_target,
    )

    try:
        # Connect to Redis
        redis_host = os.environ.get("REDIS_HOST")
        if redis_host is None:
            raise ValueError("REDIS_HOST environment variable is required")
        redis_port = int(os.environ.get("REDIS_PORT", "6379"))

        logger.info(
            "Connecting to Redis: {redis_host}:{redis_port}",
            redis_host=redis_host,
            redis_port=redis_port,
        )

        redis_conn = redis.Redis(
            host=redis_host,
            port=redis_port,
            socket_timeout=30,
            socket_connect_timeout=30,
        )

        # Test Redis connection
        ping_result = redis_conn.ping()
        logger.info("✅ Redis PING result: {ping_result}", ping_result=ping_result)

        # Enqueue the appropriate RQ job based on assignment target
        queue_name = "default"
        queue = Queue(queue_name, connection=redis_conn)

        if assignment_target == "candidate_themes":
            logger.info("Enqueueing RQ job to import candidate theme responses...")
            rq_job_name = "data_pipeline.jobs.import_candidate_theme_responses"
        else:
            logger.info("Enqueueing RQ job to import response annotations...")
            rq_job_name = "data_pipeline.jobs.import_response_annotations"

        job = queue.enqueue(
            rq_job_name,
            consultation_code,
            run_date,
            job_timeout=3_600,
        )

        logger.info(
            "✅ Successfully queued import job {job_id} ({rq_job_name}) for: {consultation_code}. "
            "Job status: {job_status}, queue '{queue_name}' now has {job_count} jobs",
            job_id=job.id,
            rq_job_name=rq_job_name,
            consultation_code=consultation_code,
            job_status=job.get_status(),
            queue_name=queue_name,
            job_count=len(queue),
        )

    except Exception as e:
        logger.exception(
            "Failed to enqueue response annotations import job: {error} ({exception_type})",
            error=str(e),
            exception_type=type(e).__name__,
        )
        raise
