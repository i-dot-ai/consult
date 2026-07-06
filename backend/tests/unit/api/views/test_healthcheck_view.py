from unittest.mock import patch

import pytest
from django.urls import reverse

from consultations.api.views.health import NOT_OK, OK

CHECK_NAMES = ("database", "redis", "s3")


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
FAILURE_CASES = [
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
        TimeoutError("Connection refused"),
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
    pytest.param(
        "s3",
        "consultations.utils.s3.get_s3_client",
        _break_s3,
        ConnectionError("S3 connection error"),
        id="s3-failure",
    ),
    pytest.param(
        "s3",
        "consultations.utils.s3.get_s3_client",
        _break_s3,
        TimeoutError("S3 connection timeout"),
        id="s3-timeout",
    ),
]


@pytest.mark.django_db
class TestHealthCheckView:
    def test_healthy_response_returns_200(self, client):
        """Test API endpoint returns expected successful response if system healthy"""
        url = reverse("health")
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == OK
        assert data["timestamp"]

    @pytest.mark.parametrize("failing_check,patch_target,apply_failure,exception", FAILURE_CASES)
    def test_dependency_failure_returns_503(
        self, client, failing_check, patch_target, apply_failure, exception
    ):
        """Test API endpoint returns 503 and marks only the failing dependency as unhealthy"""
        url = reverse("health")

        with patch(patch_target) as mock_dependency:
            apply_failure(mock_dependency, exception)
            response = client.get(url)

        assert response.status_code == 503
        data = response.json()
        assert data["status"] == NOT_OK
        for name in CHECK_NAMES:
            assert data["checks"][name] == (NOT_OK if name == failing_check else OK)
