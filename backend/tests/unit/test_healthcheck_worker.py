from datetime import timedelta

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django_rq import get_connection
from rq.utils import now, utcformat
from rq.worker import Worker


def _deregister_stray_workers(connection):
    for worker in Worker.all(connection=connection):
        worker.register_death()


@pytest.fixture(autouse=True)
def clean_worker_registry():
    """A leftover worker key from a previous failed run would false-negative these
    tests, since the command matches on hostname and the test host is fixed."""
    connection = get_connection("default")
    _deregister_stray_workers(connection)
    yield
    _deregister_stray_workers(connection)


@pytest.fixture
def rq_worker():
    worker = Worker(["default"], connection=get_connection("default"))
    worker.register_birth()
    return worker


class TestHealthcheckWorker:
    def test_fails_when_no_worker_is_registered(self):
        with pytest.raises(CommandError, match="No RQ worker registered"):
            call_command("healthcheck_worker")

    def test_succeeds_when_a_worker_has_a_fresh_heartbeat(self, rq_worker):
        call_command("healthcheck_worker")

    def test_fails_when_the_worker_heartbeat_is_stale(self, rq_worker):
        stale_heartbeat = now() - timedelta(seconds=200)
        rq_worker.connection.hset(rq_worker.key, "last_heartbeat", utcformat(stale_heartbeat))

        with pytest.raises(CommandError, match="heartbeat is stale"):
            call_command("healthcheck_worker")
