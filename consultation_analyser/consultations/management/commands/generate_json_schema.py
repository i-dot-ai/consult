import json

from django.core.management.base import BaseCommand

from consultation_analyser.consultations import public_schema


class Command(BaseCommand):
    help = "Generates JSON schema from Pydantic models"

    def handle(self, *args, **options):
        schema_folder = "./consultation_analyser/consultations/public_schema_files/"

        classes = [
            public_schema.ExecutionRun,
            public_schema.Consultation,
            public_schema.Question,
            public_schema.QuestionPart,
            public_schema.Respondent,
            public_schema.Answer,
            public_schema.Framework,
            public_schema.Theme,
            public_schema.ThemeMapping,
            public_schema.SentimentMapping,
            public_schema.EvidenceRichMapping,
        ]

        for c in classes:
            schema = c.model_json_schema()
            with open(f"{schema_folder}{c.__name__.lower()}_schema.json", "w") as f:
                json.dump(schema, f, indent=2)
