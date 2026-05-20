from django.core.management.base import BaseCommand

from consultations.dummy_data import (
    DUMMY_CONSULTATIONS,
    NUMBER_RESPONDENTS,
    create_dummy_consultation,
)


class Command(BaseCommand):
    help = "Generate dummy consultations at each pipeline stage."

    def handle(self, *args, **options):
        self.stdout.write("Generating dummy data...")
        for config in DUMMY_CONSULTATIONS:
            self.stdout.write(f"  Creating consultation: {config['CONSULTATION_NAME']}...")
            create_dummy_consultation(number_respondents=NUMBER_RESPONDENTS, config=config)
        self.stdout.write("Done.")
