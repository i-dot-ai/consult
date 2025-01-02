from django.core.management.base import BaseCommand

from consultation_analyser.factories2 import create_dummy_consultation_from_yaml


class Command(BaseCommand):
    help = "Generate a dummy consultation with 100 responses"

    def handle(self, *args, **options):
        self.stdout.write("Generating dummy data...")
        create_dummy_consultation_from_yaml(number_respondents=100)
        self.stdout.write("Done.")
