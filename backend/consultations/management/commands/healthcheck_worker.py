import socket
from datetime import datetime, timezone

from django.core.management.base import BaseCommand, CommandError
from django_rq import get_connection
from rq.worker import Worker

# RQ workers re-heartbeat roughly every DEFAULT_JOB_MONITORING_INTERVAL (30s), both while
# idle and while a job is running, so a worker that's genuinely alive never goes quiet for
# long. This threshold gives a few missed cycles of slack before treating it as hung.
STALE_HEARTBEAT_SECONDS = 120


class Command(BaseCommand):
    help = (
        "Checks that an RQ worker is registered for this host and has a recent heartbeat. "
        "Exits non-zero otherwise; intended for use as an ECS container health check."
    )

    def handle(self, *args, **options):
        connection = get_connection("default")
        hostname = socket.gethostname()

        worker = next(
            (w for w in Worker.all(connection=connection) if w.hostname == hostname), None
        )
        if worker is None:
            raise CommandError(f"No RQ worker registered for host '{hostname}'")

        if worker.last_heartbeat is None:
            raise CommandError(f"RQ worker '{worker.name}' has no recorded heartbeat")

        age_seconds = (datetime.now(timezone.utc) - worker.last_heartbeat).total_seconds()
        if age_seconds > STALE_HEARTBEAT_SECONDS:
            raise CommandError(
                f"RQ worker '{worker.name}' heartbeat is stale ({age_seconds:.0f}s old)"
            )

        self.stdout.write("ok")
