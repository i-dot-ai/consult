from django.core.management.base import BaseCommand
from django.utils.text import slugify
from consultation_analyser.consultations.dummy_data import DummyConsultation


class Command(BaseCommand):
    help = "Generate a dummy consultation with 10 responses"

    def add_arguments(self, parser):
        parser.add_argument("--name", action="store", help="The name of the consultation", type=str)

    def handle(self, *args, **options):
        self.stdout.write("Generating dummy data...")
        if options["name"]:
            name = options["name"]
            slug = slugify(name)
            DummyConsultation(name=options["name"], slug=slug)
        else:
            DummyConsultation()

        self.stdout.write("Done.")
