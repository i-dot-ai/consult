from django.core.management.base import BaseCommand

from consultation_analyser.consultations.public_schema_files.generate_openapi_yaml import (
    generate_openapi_yaml,
)


class Command(BaseCommand):
    help = "Generates YAML schema from Django models"

    def handle(self, *args, **options):
        generate_openapi_yaml()
