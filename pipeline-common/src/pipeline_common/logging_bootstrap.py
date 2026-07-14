import logging
import os

import sentry_sdk
import structlog
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

    # boto3/urllib3 log via stdlib `logging`, which StructuredLogger never configures.
    # Route it through the same structlog JSON pipeline so it isn't silently dropped
    # (root logger defaults to WARNING with no handler) or lost to stderr unformatted.
    _stdlib_handler = logging.StreamHandler()
    _stdlib_handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer("message"),
            ],
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
        )
    )
    logging.basicConfig(level=logging.INFO, handlers=[_stdlib_handler], force=True)

    logger.set_context_field("batch_job_id", os.environ.get("AWS_BATCH_JOB_ID", "unknown"))
    # Adopt the submitting Django request's context_id so both sides' logs join
    # on a single field in OpenSearch. If CONTEXT_ID is absent (e.g. the script
    # was invoked manually, outside a Batch submission), keep the context_id
    # StructuredLogger generated automatically rather than overwriting it with
    # a hardcoded "unknown".
    incoming_context_id = os.environ.get("CONTEXT_ID")
    if incoming_context_id:
        logger.set_context_field("context_id", incoming_context_id)

    # Initialize Sentry if DSN is provided
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=os.environ.get("ENVIRONMENT", "unknown"),
            traces_sample_rate=1.0,
        )
        logger.info("Sentry initialized")

    return logger
