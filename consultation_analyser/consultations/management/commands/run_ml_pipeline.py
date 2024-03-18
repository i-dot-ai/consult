# Currently a placeholder for command to run ML pipeline
from django.core.management.base import BaseCommand

from consultation_analyser.consultations import models


class Command(BaseCommand):
    help = "Run the machine learning pipeline to generate themes for the consultation"

    def add_arguments(self, parser):
        parser.add_argument("--consultation_slug", action="store", help="The slug for the consultation", type=str)

    def handle(self, *args, **options):
        if options["consultation_slug"]:
            try:
                consultation = models.Consultation.objects.get(slug=options["consultation_slug"])
                # TODO - this is to be replaced with the actual ML pipeline
                dummy_message = f"This is a placeholder for running the ML pipeline for consultation with name '{consultation.name}'"
                self.stdout.write(dummy_message)
            except models.Consultation.DoesNotExist:
                self.stdout.write("You need to enter a valid slug for a consultation")
        else:
            self.stdout.write("You need to enter the slug for a consultation")
