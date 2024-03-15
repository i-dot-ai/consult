from django.core.management import BaseCommand, call_command

from consultation_analyser.hosting_environment import HostingEnvironment


class Command(BaseCommand):
    help = "Generates an Entity Relationship Diagram for the repository’s README"

    def handle(self, *args, **options):
        if not HostingEnvironment.is_local():
            raise Exception("This command only works in the LOCAL env")

        call_command(
            "graph_models",
            ["consultations", "--pydot", "-X", "UUIDPrimaryKeyModel,TimeStampedModel", "-o", "docs/erd.png"],
        )
