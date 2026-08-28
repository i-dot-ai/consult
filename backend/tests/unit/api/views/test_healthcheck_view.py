from unittest.mock import patch

import pytest
from django.urls import reverse

from consultations.api.views.health import NOT_OK, OK

CRITICAL_CHECK_NAMES = ("database", "redis")
ALL_CHECK_NAMES = ("database", "redis", "s3")


def _break_database(mock_connect, exception):
    mock_connect.side_effect = exception


def _break_redis(mock_redis, exception):
    mock_redis.return_value.ping.side_effect = exception


def _break_s3(mock_s3, exception):
    mock_s3.return_value.head_bucket.side_effect = exception


# Cases for test parametrisation to mock different errors:
# * failing_check: which component will break
# * patch_target: the dependency used by the healthcheck
# * apply_failure: where the exception is invoked
# * exception: either ConnectionError or TimeoutError
CRITICAL_FAILURE_CASES = [
    pytest.param(
        "database",
        "consultations.api.views.health.psycopg.connect",
        _break_database,
        ConnectionError("Connection refused"),
        id="db-failure",
    ),
    pytest.param(
        "database",
        "consultations.api.views.health.psycopg.connect",
        _break_database,
        TimeoutError("Connection timed out"),
        id="db-timeout",
    ),
    pytest.param(
        "redis",
        "redis.Redis.from_url",
        _break_redis,
        ConnectionError("Connection refused"),
        id="redis-failure",
    ),
    pytest.param(
        "redis",
        "redis.Redis.from_url",
        _break_redis,
        TimeoutError("Redis TimeoutError"),
        id="redis-timeout",
    ),
]

S3_FAILURE_CASES = [
    pytest.param(
        ConnectionError("S3 connection error"),
        id="s3-failure",
    ),
    pytest.param(
        TimeoutError("S3 connection timeout"),
        id="s3-timeout",
    ),
]


@pytest.mark.django_db
class TestHealthCheckView:
    def test_healthy_response_returns_200(self, client):
        """Returns 200 with all checks passing when all dependencies are reachable."""
        url = reverse("health")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == OK
        assert data["timestamp"]
        for name in ALL_CHECK_NAMES:
            assert data["checks"][name] == OK

    @pytest.mark.parametrize("failing_check,patch_target,apply_failure,exception", CRITICAL_FAILURE_CASES)
    def test_critical_dependency_failure_returns_503(
        self, client, failing_check, patch_target, apply_failure, exception
    ):
        """Returns 503 and marks only the failing critical dependency as unhealthy."""
        url = reverse("health")

        with patch(patch_target) as mock_dependency:
            apply_failure(mock_dependency, exception)
            response = client.get(url)

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == NOT_OK
        for name in CRITICAL_CHECK_NAMES:
            assert data["checks"][name] == (NOT_OK if name == failing_check else OK)

    @pytest.mark.parametrize("exception", S3_FAILURE_CASES)
    def test_s3_failure_returns_200_with_degraded_s3_status(self, client, exception):
        """S3 is non-critical: its failure is reported in checks but does not cause a 503."""
        url = reverse("health")

        with patch("consultations.utils.s3.get_s3_client") as mock_s3:
            _break_s3(mock_s3, exception)
            response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == OK
        assert data["checks"]["s3"] == NOT_OK
        assert data["checks"]["database"] == OK
        assert data["checks"]["redis"] == OK


@pytest.mark.django_db
class TestLiveCheckView:
    def test_returns_200_when_process_is_running(self, client):
        """Always returns 200 regardless of dependency state."""
        url = reverse("live")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == OK
        assert data["timestamp"]

    def test_requires_no_authentication(self, client):
        """Liveness probe must be accessible without any credentials."""
        url = reverse("live")
        response = client.get(url)

        assert response.status_code == 200
