from django.core.management.base import BaseCommand

from consultation_analyser.consultations.dummy_data import create_dummy_consultation_from_yaml


class Command(BaseCommand):
    help = (
        "Generate two dummy consultations, one at theme sign off stage and one at analysis stage."
    )

    def handle(self, *args, **options):
        self.stdout.write("Generating dummy data...")
        create_dummy_consultation_from_yaml(
            number_respondents=100, consultation_stage="theme_sign_off"
        )
        create_dummy_consultation_from_yaml(number_respondents=100, consultation_stage="analysis")
        self.stdout.write("Done.")
