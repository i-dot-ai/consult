# Dummy command to test the batch job
# TODO - delete once we know that batch job is running
from django.core.management.base import BaseCommand

from consultation_analyser.consultations import models


class Command(BaseCommand):
    help = "Very basic management command to test batch job"

    def handle(self, *args, **options):
        dummy_message = "Hi, I am a mangement command that just outputs a string."
        self.stdout.write(dummy_message)

