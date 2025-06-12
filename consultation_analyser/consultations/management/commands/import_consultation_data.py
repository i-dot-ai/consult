import json
import os

import boto3
import pandas as pd
from django.core.management.base import BaseCommand

from consultation_analyser.consultations.models import (
    Answer,
    ConsultationOld,
    ExecutionRun,
    Framework,
    QuestionOld,
    QuestionPart,
    RespondentOld,
    ThemeMapping,
    ThemeOld,
)


class Command(BaseCommand):
    help = "Import data from an S3 bucket"

    def add_arguments(self, parser):
        parser.add_argument("key_prefix", nargs="+", type=str)

    def handle(self, *args, **options):
        self.stdout.write("Importing data")

        key_prefix = options["key_prefix"][0]

        question_key = f"{key_prefix}/expanded_question.txt"
        themes_key = f"{key_prefix}/topics.json"
        responses_key = f"{key_prefix}/q1_ai_output.xlsx"

        s3 = boto3.client(
            "s3",
        )
        question_response = s3.get_object(Bucket=os.environ["AWS_BUCKET_NAME"], Key=question_key)
        themes_response = s3.get_object(Bucket=os.environ["AWS_BUCKET_NAME"], Key=themes_key)

        question_text = question_response.get("Body").read().decode("utf-8")
        theme_dict = json.loads(themes_response["Body"].read())

        consultation = ConsultationOld.objects.create(title="Test Consultation")
        question = QuestionOld.objects.create(
            consultation=consultation,
            text=question_text,
            number=1,
        )
        self.stdout.write(f"Successfully saved question {question.text}")

        question_part = QuestionPart.objects.create(
            question=question,
            number=1,
            type=QuestionPart.QuestionType.FREE_TEXT,
        )
        self.stdout.write("Successfully created free text question part")

        # Add themes
        execution_run = ExecutionRun.objects.create(type=ExecutionRun.TaskType.THEME_MAPPING)
        framework = Framework.create_initial_framework(
            execution_run=execution_run, question_part=question_part
        )
        theme_object_lookup = {}

        for key, value in theme_dict.items():
            theme = ThemeOld.create_initial_theme(
                framework=framework,
                name=value["topic_name"],
                description=value["rationale"],
                key=key,
            )
            theme_object_lookup[key] = theme.id
            self.stdout.write(f"Successfully saved theme {theme.name}")

        self.stdout.write(f"Theme lookup dict: {theme_object_lookup}")

        # Get answers and theme mappings
        answer_response = s3.get_object(Bucket=os.environ["AWS_BUCKET_NAME"], Key=responses_key)

        answer_df = pd.read_excel(answer_response["Body"].read())

        for _, row in answer_df.iterrows():
            respondent = RespondentOld.objects.create(
                consultation=consultation,
            )

            response = Answer.objects.create(
                question_part=question_part, respondent=respondent, text=row["Response"]
            )

            if isinstance(row["Positive Topics"], str):
                for theme_key in row["Positive Topics"].split(","):
                    theme_id = theme_object_lookup[theme_key]
                    ThemeMapping.objects.create(
                        answer=response,
                        theme_id=theme_id,
                        execution_run=execution_run,
                        stance=ThemeMapping.Stance.POSITIVE,
                    )

            if isinstance(row["Negative Topics"], str):
                for theme_key in row["Negative Topics"].split(","):
                    theme_id = theme_object_lookup[theme_key]
                    ThemeMapping.objects.create(
                        answer=response,
                        theme_id=theme_id,
                        execution_run=execution_run,
                        stance=ThemeMapping.Stance.NEGATIVE,
                    )
            self.stdout.write(f"Successfully added response topics for {response.id}")
