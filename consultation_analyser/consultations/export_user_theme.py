import csv
import datetime
import logging
import os
import uuid
from io import StringIO

import boto3
from django.conf import settings
from django_rq import job

from consultation_analyser.consultations.models import (
    Answer,
    Consultation,
    ExecutionRun,
    QuestionPart,
    SentimentMapping,
    ThemeMapping,
)

logger = logging.getLogger("export")


def get_timestamp() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d-%H%M%S")


def get_latest_sentiment_execution_run_for_question_part(
    question_part: QuestionPart,
) -> ExecutionRun | None:
    sentiment_qs = SentimentMapping.objects.select_related("execution_run").filter(
        answer__question_part=question_part,
        execution_run__type=ExecutionRun.TaskType.SENTIMENT_ANALYSIS,
    )
    execution_run_ids = sentiment_qs.values_list("execution_run", flat=True)
    execution_runs = ExecutionRun.objects.filter(id__in=execution_run_ids)

    if execution_runs:
        return execution_runs.order_by("created_at").last()
    return None


def get_position(answer: Answer, execution_run: ExecutionRun | None) -> str | None:
    if not execution_run:
        return None
    sentiment = SentimentMapping.objects.filter(answer=answer, execution_run=execution_run)
    if sentiment:
        # There will only be one
        return sentiment.first().position
    return None


def get_theme_mapping_output_row(
    mappings_for_framework: ThemeMapping,
    historical_mappings_for_framework: ThemeMapping.history.model,
    response: Answer,
    sentiment_execution_run: ExecutionRun | None,
) -> dict:
    # Default to theme mappings for latest framework
    question_part = response.question_part
    question = question_part.question
    consultation_title = question.consultation.title

    position = get_position(answer=response, execution_run=sentiment_execution_run)

    original_themes = (
        historical_mappings_for_framework.filter(answer=response)
        .filter(user_audited=False)
        .filter(history_type="+")
    )
    original_themes_identifiers = {tm.theme.get_identifier(): tm.stance for tm in original_themes}
    ordered_theme_identifiers = sorted(list(original_themes_identifiers.keys()))

    current_themes = mappings_for_framework.filter(answer=response).filter(user_audited=True)
    auditors = set(
        [r.history_user.email for r in response.history.filter(is_theme_mapping_audited=True)]
    )
    row_data = {
        "Response ID": response.respondent.themefinder_respondent_id,
        "Consultation": consultation_title,
        "Question number": question.number,
        "Question text": question.text,
        "Question part text": question_part.text,
        "Response text": response.text,
        "Response has been audited": response.is_theme_mapping_audited,
        "Original themes": ", ".join(ordered_theme_identifiers),
        "Current themes": ", ".join(
            sorted([theme_mapping.theme.get_identifier() for theme_mapping in current_themes])
        ),
        "Position": position,
        "Auditors": ", ".join(list(auditors)),
        "First audited at": response.datetime_theme_mapping_audited,  # First time audited
    }
    return row_data


def get_theme_mapping_rows(question_part: QuestionPart) -> list[dict]:
    output = []
    # Default to latest execution run
    sentiment_run = get_latest_sentiment_execution_run_for_question_part(question_part)
    answer_qs = Answer.objects.filter(question_part=question_part)
    # Get themes from latest framework
    current_theme_mappings = ThemeMapping.get_latest_theme_mappings(
        question_part=question_part, history=False
    )
    historical_theme_mappings = ThemeMapping.get_latest_theme_mappings(
        question_part=question_part, history=True
    )
    for response in answer_qs:
        row = get_theme_mapping_output_row(
            mappings_for_framework=current_theme_mappings,
            historical_mappings_for_framework=historical_theme_mappings,
            response=response,
            sentiment_execution_run=sentiment_run,
        )
        output.append(row)
    return output



# def get_theme_mapping_output(consultation: Consultation, question_part: QuestionPart) -> list[dict]:
#     output = []
#     for question_part in QuestionPart.objects.filter(
#         question__consultation=consultation,
#         type=QuestionPart.QuestionType.FREE_TEXT,
#     ):
#         # Default to latest execution run
#         sentiment_run = get_latest_sentiment_execution_run_for_question_part(question_part)
#         answer_qs = Answer.objects.filter(question_part=question_part)
#         # Get themes from latest framework
#         current_theme_mappings = ThemeMapping.get_latest_theme_mappings(
#             question_part=question_part, history=False
#         )
#         historical_theme_mappings = ThemeMapping.get_latest_theme_mappings(
#             question_part=question_part, history=True
#         )
#         for response in answer_qs:
#             row = get_theme_mapping_output_row(
#                 mappings_for_framework=current_theme_mappings,
#                 historical_mappings_for_framework=historical_theme_mappings,
#                 response=response,
#                 sentiment_execution_run=sentiment_run,
#             )
#             output.append(row)
#     return output


def export_user_theme(question_part_id: uuid.UUID, s3_key: str) -> None:
    question_part = QuestionPart.objects.get(id=question_part_id)
    output = get_theme_mapping_rows(question_part)
    timestamp = get_timestamp()
    # unique as only one free text question part per question
    question_number = question_part.question.number
    filename = f"{timestamp}_question_{question_number}_theme_changes.csv"

    if settings.ENVIRONMENT == "local":
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        with open(
            f"downloads/{filename}", mode="w"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=output[0].keys())
            writer.writeheader()
            for row in output:
                writer.writerow(row)
    else:
        if len(s3_key) == 0:
            raise ValueError("s3_key cannot be empty")

        s3_client = boto3.client("s3")

        csv_buffer = StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=output[0].keys())
        writer.writeheader()
        for row in output:
            writer.writerow(row)

        s3_client.put_object(
            Bucket=settings.AWS_BUCKET_NAME,
            Key=f"{s3_key}/{filename}",
            Body=csv_buffer.getvalue(),
        )
        csv_buffer.close()
    logger.info(f"Finishing export for question {question_number} for consultation {question_part.question.consultation.title}")


@job("default", timeout=900)
def export_user_theme_job(question_part_id: str, s3_key: str) -> None:
    export_user_theme(question_part_id, s3_key)
