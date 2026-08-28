from collections.abc import Callable
from datetime import UTC, datetime

import psycopg
import redis
from botocore.config import Config
from django.conf import settings
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from consultations.utils import s3 as s3_utils

logger = settings.LOGGER

OK = "ok"
NOT_OK = "error"
CHECK_TIMEOUT_SECONDS = 5


def _run_check(checks: dict[str, str], name: str, check: Callable[[], None]) -> None:
    try:
        check()
        checks[name] = OK
    except Exception:
        checks[name] = NOT_OK
        logger.exception("{check_name} healthcheck error", check_name=name.capitalize())


def _check_database() -> None:
    conn_params = connection.get_connection_params()
    conn_params["connect_timeout"] = CHECK_TIMEOUT_SECONDS
    conn = psycopg.connect(**conn_params)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SET statement_timeout = {CHECK_TIMEOUT_SECONDS * 1000}")
            cursor.execute("SELECT 1")
    finally:
        conn.close()


def _check_redis() -> None:
    redis_client = redis.Redis.from_url(
        settings.CACHES["redis"]["LOCATION"],
        socket_connect_timeout=CHECK_TIMEOUT_SECONDS,
        socket_timeout=CHECK_TIMEOUT_SECONDS,
    )
    try:
        redis_client.ping()
    finally:
        redis_client.close()


def _check_s3() -> None:
    s3_client = s3_utils.get_s3_client(
        config=Config(
            connect_timeout=CHECK_TIMEOUT_SECONDS,
            read_timeout=CHECK_TIMEOUT_SECONDS,
        )
    )
    params = {"Bucket": settings.AWS_BUCKET_NAME}
    if settings.ENVIRONMENT.upper() not in ["LOCAL", "TEST"]:
        params["ExpectedBucketOwner"] = settings.AWS_ACCOUNT_ID
    s3_client.head_bucket(**params)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(_request) -> Response:
    """Check health of connected services.

    S3 is treated as a non-critical dependency: its status is reported but does
    not affect the overall health status or HTTP response code.
    """
    critical_checks: dict[str, str] = {}
    non_critical_checks: dict[str, str] = {}

    _run_check(critical_checks, "database", _check_database)
    _run_check(critical_checks, "redis", _check_redis)
    _run_check(non_critical_checks, "s3", _check_s3)

    app_status = OK if all(v == OK for v in critical_checks.values()) else NOT_OK
    http_status = 200 if app_status == OK else 503

    return Response(
        {
            "status": app_status,
            "checks": {**critical_checks, **non_critical_checks},
            "timestamp": datetime.now(UTC).isoformat(),
        },
        status=http_status,
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def live_check(_request) -> Response:
    """Liveness probe — returns 200 whenever the process is running."""
    return Response(
        {"status": OK, "timestamp": datetime.now(UTC).isoformat()},
        status=200,
    )
