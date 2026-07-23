import os

import sentry_sdk
from i_dot_ai_utilities.logging.structured_logger import StructuredLogger
from i_dot_ai_utilities.logging.types.enrichment_types import ExecutionEnvironmentType
from i_dot_ai_utilities.logging.types.log_output_format import LogOutputFormat


def bootstrap_logger() -> StructuredLogger:
    # The Fargate enricher reads ECS_CONTAINER_METADATA_URI_V4, which only exists on Fargate.
    _execution_environment = (
        ExecutionEnvironmentType.FARGATE
        if os.environ.get("EXECUTION_CONTEXT") == "batch"
        else ExecutionEnvironmentType.LOCAL
    )

    logger = StructuredLogger(
        level="info",
        options={
            "execution_environment": _execution_environment,
            "log_format": LogOutputFormat.JSON,
            "ship_logs": True,
        },
    )

    logger.set_context_field(
        "execution_context", os.environ.get("EXECUTION_CONTEXT", "batch")
    )
    logger.set_context_field(
        "batch_job_id", os.environ.get("AWS_BATCH_JOB_ID", "unknown")
    )

    # Initialize Sentry if DSN is provided
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.environ.get("ENVIRONMENT", "unknown"),
            traces_sample_rate=1.0,
        )

    return logger
