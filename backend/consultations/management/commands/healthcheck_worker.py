import socket
from datetime import UTC, datetime

import redis
from django.core.management.base import BaseCommand, CommandError
from django_rq import get_connection
from rq.defaults import DEFAULT_WORKER_TTL
from rq.worker import Worker

# A worker only re-heartbeats every ~30s while a job is running. While idle - its normal
# state - RQ's dequeue loop blocks for up to worker_ttl - 15 (~405s by default) between
# heartbeats, so basing the threshold on worker_ttl (rather than the job-monitoring
# interval) avoids false positives on healthy idle workers. This is RQ's *default*
# worker_ttl, not something read from the live worker; if start-worker.sh ever overrides
# it, update this too.
STALE_HEARTBEAT_SECONDS = DEFAULT_WORKER_TTL + 120


class Command(BaseCommand):
    help = (
        "Checks that an RQ worker is registered for this host and has a recent heartbeat. "
        "Exits non-zero otherwise; intended for use as an ECS container health check."
    )

    def handle(self, *args, **options):
        connection = get_connection("default")
        hostname = socket.gethostname()

        try:
            worker = next(
                (w for w in Worker.all(connection=connection) if w.hostname == hostname), None
            )
        except redis.exceptions.RedisError as exc:
            raise CommandError(f"Could not reach Redis: {exc}") from exc
        if worker is None:
            raise CommandError(f"No RQ worker registered for host '{hostname}'")

        if worker.last_heartbeat is None:
            raise CommandError(f"RQ worker '{worker.name}' has no recorded heartbeat")

        age_seconds = (datetime.now(UTC) - worker.last_heartbeat).total_seconds()
        if age_seconds > STALE_HEARTBEAT_SECONDS:
            raise CommandError(
                f"RQ worker '{worker.name}' heartbeat is stale ({age_seconds:.0f}s old)"
            )

        self.stdout.write("ok")
