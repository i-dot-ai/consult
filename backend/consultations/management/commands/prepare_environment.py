from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections


class Command(BaseCommand):
    help = "Prepare the environment: runs migrations on prod; resets and seeds the database and S3 on dev and preprod."

    def handle(self, *args, **options):
        environment = getattr(settings, "ENVIRONMENT", "").lower()

        if environment == "prod":
            self.stdout.write("Running migrate on prod.")
            call_command("migrate", verbosity=1)
            return

        self.stdout.write(f"Resetting database on {environment}...")
        connection = connections["default"]
        with connection.cursor() as cursor:
            cursor.execute("DROP SCHEMA public CASCADE;")
            cursor.execute("CREATE SCHEMA public;")

        call_command("migrate", verbosity=1)
        call_command("createadminusers", verbosity=1)
        call_command("generate_dummy_data", verbosity=1)
        call_command("prepare_s3", verbosity=1)
        self.stdout.write("Environment prepared.")
