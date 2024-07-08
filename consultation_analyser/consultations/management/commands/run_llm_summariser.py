from django.core.management.base import BaseCommand

from consultation_analyser.consultations import models
from consultation_analyser.pipeline.processing import summarise_with_llm


class Command(BaseCommand):
    help = "Run the LLM summariser to generate improved summaries for themes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--consultation_slug", action="store", help="The slug for the consultation", type=str
        )

    def handle(self, *args, **options):
        if options["consultation_slug"]:
            try:
                consultation = models.Consultation.objects.get(slug=options["consultation_slug"])
                summarise_with_llm(consultation)
                self.stdout.write(
                    f"LLM summariser has been run for consultation with name {consultation.name}"
                )
            except models.Consultation.DoesNotExist:
                self.stdout.write("You need to enter a valid slug for a consultation")
        else:
            self.stdout.write("You need to enter the slug for a consultation")
