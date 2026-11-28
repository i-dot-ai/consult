from uuid import UUID

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from consultations.models import Consultation
from consultations.services.migrate_v1_to_v2 import (
    audit_consultation,
    migrate_consultation_to_v2,
)

logger = settings.LOGGER


class Command(BaseCommand):
    help = (
        "Run the v1 to v2 migration for every consultation that has not been migrated, "
        "one transaction each. With --dry-run nothing is written and the exit code is "
        "non-zero while any consultation is unmigrated."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument(
            "--consultation",
            help=(
                "Only this consultation id, even if it has already been migrated: a dry run "
                "still reports it, and a real run makes no further changes to it"
            ),
        )

    def handle(self, *args, **options):
        consultations = Consultation.objects.order_by("created_at")
        if options["consultation"]:
            try:
                consultation_id = UUID(options["consultation"])
            except ValueError:
                raise CommandError(f"{options['consultation']} is not a consultation id") from None
            consultations = consultations.filter(id=consultation_id)
            if not consultations.exists():
                raise CommandError(f"Consultation {options['consultation']} does not exist")
        else:
            consultations = consultations.filter(migrated_at__isnull=True)

        if options["dry_run"]:
            self.report(consultations)
            return

        migrated = 0
        failed = []
        for consultation in consultations:
            if consultation.migrated_at is not None:
                self.stdout.write(f"Already migrated {consultation.id} ({consultation.title})")
                continue
            try:
                migrate_consultation_to_v2(consultation)
            except Exception:
                logger.exception(
                    "Migration failed for consultation {consultation_id}",
                    consultation_id=consultation.id,
                )
                failed.append(consultation)
                continue
            migrated += 1
            self.stdout.write(f"Migrated {consultation.id} ({consultation.title})")

        self.stdout.write(f"{migrated} migrated, {len(failed)} failed")
        if failed:
            raise CommandError(
                "Migration failed for: "
                + ", ".join(str(consultation.id) for consultation in failed)
            )

    def report(self, consultations):
        unmigrated = 0
        for consultation in consultations:
            if consultation.migrated_at is None:
                unmigrated += 1
            self.stdout.write(
                f"{consultation.id} ({consultation.title}): migrated_at={consultation.migrated_at}"
            )
            for key, value in audit_consultation(consultation).items():
                if value:
                    self.stdout.write(f"  {key}: {value}")

        self.stdout.write(f"{unmigrated} consultations unmigrated")
        if unmigrated:
            raise CommandError("Unmigrated consultations remain; nothing was changed")
