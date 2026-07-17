import datetime
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


def _epoch_ms_to_iso(epoch_ms: int | None) -> str | None:
    """Convert an AWS Batch epoch-millisecond timestamp to an ISO-8601 string."""
    if epoch_ms is None:
        return None
    return datetime.datetime.fromtimestamp(epoch_ms / 1000, tz=datetime.UTC).isoformat()


def lambda_handler(event, context):
    """
    Lambda triggered by EventBridge when find themes batch job completes.

    Enqueues a Django RQ job to import the candidate themes from S3 to the database.
    """
    logger.refresh_context([{"type": ContextEnrichmentType.LAMBDA, "object": context}])

    detail = event["detail"]
    job_name = detail["jobName"]
    job_status = detail["status"]
    start_date_time = _epoch_ms_to_iso(detail.get("startedAt"))
    end_date_time = _epoch_ms_to_iso(detail.get("stoppedAt"))

    parameters = detail["parameters"]
    consultation_code = parameters["consultation_code"]
    run_date = parameters["run_date"]
    user_id = parameters.get("user_id")
    model_name = parameters.get("model_name")

    logger.set_context_field("batch_job_name", job_name)
    logger.set_context_field("consultation_code", consultation_code)

    logger.info(
        "Batch job '{job_name}' completed with status: {job_status} consultation_code: {consultation_code} "
        "start_date_time: {start_date_time} end_date_time: {end_date_time}",
        job_name=job_name,
        job_status=job_status,
        consultation_code=consultation_code,
        start_date_time=start_date_time,
        end_date_time=end_date_time,
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

        # Enqueue the RQ job
        queue_name = "default"
        queue = Queue(queue_name, connection=redis_conn)
        logger.info("Enqueueing RQ job to import candidate themes...")
        job = queue.enqueue(
            "data_pipeline.jobs.import_candidate_themes",
            consultation_code,
            run_date,
            user_id,
            model_name,
        )

        logger.info(
            "✅ Successfully queued candidate themes import job {job_id} for: {consultation_code}. "
            "Job status: {job_status}, queue '{queue_name}' now has {job_count} jobs",
            job_id=job.id,
            consultation_code=consultation_code,
            job_status=job.get_status(),
            queue_name=queue_name,
            job_count=len(queue),
        )

    except Exception:
        logger.exception("Failed to enqueue candidate themes import job")
        raise
