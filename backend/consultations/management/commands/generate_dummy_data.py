from django.core.management.base import BaseCommand

from consultations.dummy_data import create_dummy_consultation_from_yaml
from consultations.models import Consultation


class Command(BaseCommand):
    help = (
        "Generate two dummy consultations, one at theme sign off stage and one at analysis stage."
    )

    def handle(self, *args, **options):
        self.stdout.write("Generating dummy data...")
        create_dummy_consultation_from_yaml(
            number_respondents=100, consultation_stage=Consultation.Stage.THEME_SIGN_OFF
        )
        create_dummy_consultation_from_yaml(
            number_respondents=100, consultation_stage=Consultation.Stage.ANALYSIS
        )
        self.stdout.write("Done.")
