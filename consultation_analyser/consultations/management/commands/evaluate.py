import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from consultation_analyser.authentication.models import User
from consultation_analyser.consultations import models
from consultation_analyser.consultations.download_consultation import consultation_to_json
from consultation_analyser.consultations.upload_consultation import upload_consultation
from consultation_analyser.pipeline.backends.bertopic import BERTopicBackend
from consultation_analyser.pipeline.backends.dummy_llm_backend import DummyLLMBackend
from consultation_analyser.pipeline.backends.dummy_topic_backend import DummyTopicBackend
from consultation_analyser.pipeline.backends.ollama_llm_backend import OllamaLLMBackend
from consultation_analyser.pipeline.backends.sagemaker_llm_backend import SagemakerLLMBackend
from consultation_analyser.pipeline.processing import process_consultation_themes


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
            "--llm",
            action="store",
            help="The llm to use for summarising. Will be fake by default. Pass 'sagemaker' or 'ollama/model' to specify a model",
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
            print("Removed original consultation")

        try:
            consultation = upload_consultation(open(input_file), user)
        except IntegrityError as e:
            print(e)
            print(
                "This consultation already exists. To remove it and start with a fresh copy pass --clean."
            )
            exit()

        input_file = options["input"]
        if not input_file:
            raise Exception("You need to specify an input file")

        embedding_model = options.get("embedding_model", None)
        if embedding_model == "fake":
            topic_backend = DummyTopicBackend()
            print(f"Using {embedding_model} for BERTopic embeddings")
        else:
            topic_backend = BERTopicBackend()
            print(
                f"Using default {settings.BERTOPIC_DEFAULT_EMBEDDING_MODEL} for BERTopic embeddings"
            )

        llm_choice = options.get("llm", "fake")

        if llm_choice == "fake" or not llm_choice:
            llm_backend = DummyLLMBackend()
        elif llm_choice == "sagemaker":
            llm_backend = SagemakerLLMBackend()
        elif llm_choice.startswith("ollama"):
            model = llm_choice.split("/")[1]
            llm_backend = OllamaLLMBackend(model)
        else:
            raise Exception(f"Invalid --llm specified: {llm_choice}")

        process_consultation_themes(
            consultation, topic_backend=topic_backend, llm_backend=llm_backend
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
