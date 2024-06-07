import os
import json

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.utils import IntegrityError

from consultation_analyser.consultations import models
from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.consultations.download_consultation import consultation_to_json

from consultation_analyser.pipeline.processing import process_consultation_themes

from consultation_analyser.authentication.models import User

from langchain_community.llms.fake import FakeListLLM


class Command(BaseCommand):
    help = "Run the pipeline, write evaluation JSON"

    def add_arguments(self, parser):
        parser.add_argument(
            "--input",
            action="store",
            help="A path to a JSON file containing a ConsultationWithResponses",
            type=str,
        )
        parser.add_argument(
            "--embedding_model",
            action="store",
            help="The embedding model to use in BERTopic. Pass 'fake' to get fake topics",
            type=str,
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Whether to delete an existing matching consultation first",
        )

    def handle(self, *args, **options):
        input_file = options["input"]
        if not input_file:
            raise Exception("You need to specify an input file")

        # TODO deal with existing consultation and make sure user knows it will be deleted

        user = User.objects.filter(email="email@example.com").first()
        # upload the consultation

        clean = options["clean"]
        if clean:
            input_json = json.loads(open(input_file).read())
            name = input_json["consultation"]["name"]
            old_consultation = models.Consultation.objects.get(name=name)
            old_consultation.delete()

        try:
            consultation = upload_consultation(open(input_file), user)
        except IntegrityError as e:
            print(e)
            print (
                "This consultation already exists. To remove it and start with a fresh copy pass --clean."
            )
            exit()

        input_file = options["input"]
        if not input_file:
            raise Exception("You need to specify an input file")

        embedding_model = options.get("embedding_model", "thenlper/gte-small")

        llm = FakeListLLM(responses=[
            '{"short description": "Example short description", "summary": "Example summary"}'
        ])
        process_consultation_themes(
            consultation, embedding_model_name=embedding_model, llm=llm
        )

        # export it to JSON
        json_with_themes = consultation_to_json(consultation)

        # write it to a well known place
        output_dir = settings.BASE_DIR / "tmp" / "eval" / consultation.slug
        os.makedirs(output_dir, exist_ok=True)

        f = open(output_dir / "consultation_with_themes.json", "w")
        f.write(json_with_themes)
        f.close()

        print(f"Output: {output_dir / 'consultation_with_themes.json'}")
