from django.core.management.base import BaseCommand

from consultation_analyser.consultations import models
from consultation_analyser.pipeline.processing import process_consultation_themes

from consultation_analyser.pipeline.llm_summariser import create_llm_summaries_for_consultation

class Command(BaseCommand):
    def handle(self, *args, **options):
        consultation = models.Consultation.objects.first()
        process_consultation_themes(consultation)
        create_llm_summaries_for_consultation(consultation)
