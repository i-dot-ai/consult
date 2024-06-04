import json

from django.core.management import BaseCommand

from consultation_analyser.consultations import public_schema


class Command(BaseCommand):
    help = "Generates JSON schema"

    def handle(self, *args, **options):
        schema_folder = "./consultation_analyser/consultations/public_schema"

        schema = public_schema.Consultation.model_json_schema()
        with open(f"{schema_folder}/consultation_schema.json", "w") as f:
            json.dump(schema, f)

        schema = public_schema.ConsultationResponse.model_json_schema()
        with open(f"{schema_folder}/consultation_response_schema.json", "w") as f:
            json.dump(schema, f)

        schema = public_schema.ConsultationWithResponses.model_json_schema()
        with open(f"{schema_folder}/consultation_with_responses_schema.json", "w") as f:
            json.dump(schema, f)

        schema = public_schema.ConsultationWithResponsesAndThemes.model_json_schema()
        with open(f"{schema_folder}/consultation_with_responses_and_themes_schema.json", "w") as f:
            json.dump(schema, f)
