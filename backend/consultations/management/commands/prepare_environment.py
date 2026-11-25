from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections

from consultations.models import Consultation
from hosting_environment import HostingEnvironment


class Command(BaseCommand):
    help = "Prepare the environment: runs migrations everywhere; also seeds admin users and dummy data into an empty database on local/test; resets and seeds the database and S3 on deployed dev only."

    def handle(self, *args, **options):
        environment = getattr(settings, "ENVIRONMENT", "").lower()

        if not HostingEnvironment.is_development_environment():
            self.stdout.write(f"Running migrate on {environment}.")
            call_command("migrate", verbosity=1)
            return

        is_dev = HostingEnvironment.is_dev()
        if is_dev:
            self.stdout.write(f"Resetting database on {environment}...")
            connection = connections["default"]
            with connection.cursor() as cursor:
                cursor.execute("DROP SCHEMA public CASCADE;")
                cursor.execute("CREATE SCHEMA public;")

        call_command("migrate", verbosity=1)
        call_command("createadminusers", verbosity=1)
        # Local/test keep their data, so only seed an empty database to avoid duplicates
        if is_dev or not Consultation.objects.exists():
            call_command("generate_dummy_data", verbosity=1)

        if is_dev:
            call_command("prepare_s3", verbosity=1)

        self.stdout.write("Environment prepared.")
