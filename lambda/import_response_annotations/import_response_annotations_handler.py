import logging
import os

import redis  # type: ignore
from rq import Queue

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, _context):
    """
    Lambda triggered by EventBridge when assign themes batch job completes.

    Enqueues a Django RQ job to import response annotations from S3 to the database.
    """

    detail = event["detail"]
    job_name = detail["jobName"]
    job_status = detail["status"]

    parameters = detail["parameters"]
    consultation_code = parameters["consultation_code"]
    run_date = parameters["run_date"]
    assignment_target = parameters.get("assignment_target", "selected_themes")

    logger.info(f"Batch job '{job_name}' completed with status: {job_status}")
    logger.info(f"Consultation code: {consultation_code}")
    logger.info(f"Run date: {run_date}")
    logger.info(f"Assignment target: {assignment_target}")

    try:
        # Connect to Redis
        redis_host = os.environ.get("REDIS_HOST")
        redis_port = int(os.environ.get("REDIS_PORT", "6379"))

        logger.info(f"Connecting to Redis: {redis_host}:{redis_port}")

        redis_conn = redis.Redis(
            host=redis_host,
            port=redis_port,
            socket_timeout=30,
            socket_connect_timeout=30,
        )

        # Test Redis connection
        ping_result = redis_conn.ping()
        logger.info(f"✅ Redis PING result: {ping_result}")

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

        logger.info("✅ RQ job enqueued successfully!")
        logger.info(f"Job ID: {job.id}")
        logger.info(f"Job function: {rq_job_name}")
        logger.info(f"Job status: {job.get_status()}")
        logger.info(f"Queue '{queue_name}' now has {len(queue)} jobs")

        logger.info(
            f"✅ Successfully queued import job {job.id} for: {consultation_code}"
        )

    except Exception as e:
        error_msg = f"Failed to enqueue response annotations import job: {str(e)}"
        logger.error(f"ERROR: {error_msg}")
        logger.error(f"Exception type: {type(e).__name__}")
        raise
