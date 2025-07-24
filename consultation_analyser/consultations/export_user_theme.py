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
    Question,
    Response,
    ResponseAnnotation,
)

logger = logging.getLogger("export")


def get_timestamp() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d-%H%M%S")


def get_position(response: Response) -> str | None:
    # In the new model, sentiment is stored directly in ResponseAnnotation
    try:
        annotation = response.annotation
        return annotation.sentiment
    except ResponseAnnotation.DoesNotExist:
        return None


def get_theme_mapping_output_row(
    response: Response,
) -> dict:
    # In new model, themes are stored as ManyToMany with through table tracking original vs current
    question = response.question
    consultation_title = question.consultation.title

    position = get_position(response=response)

    # Get original and current themes from the annotation
    original_themes = []
    current_themes = []
    audited = False
    auditor_email = None
    reviewed_at = None

    try:
        annotation = response.annotation
        original_themes = annotation.get_original_ai_themes()
        current_themes = (
            annotation.get_human_reviewed_themes()
            if annotation.human_reviewed
            else annotation.get_original_ai_themes()
        )
        audited = annotation.human_reviewed
        if annotation.reviewed_by:
            auditor_email = annotation.reviewed_by.email
        reviewed_at = annotation.reviewed_at
    except ResponseAnnotation.DoesNotExist:
        pass

    # Build theme identifiers
    original_theme_identifiers = []
    for theme in original_themes:
        identifier = theme.key if theme.key else theme.name
        original_theme_identifiers.append(identifier)

    current_theme_identifiers = []
    for theme in current_themes:
        identifier = theme.key if theme.key else theme.name
        current_theme_identifiers.append(identifier)

    row_data = {
        "Response ID": response.respondent.themefinder_id,
        "Consultation": consultation_title,
        "Question number": question.number,
        "Question text": question.text,
        "Response text": response.free_text,
        "Response has been audited": audited,
        "Original themes": ", ".join(sorted(original_theme_identifiers)),
        "Current themes": ", ".join(sorted(current_theme_identifiers)),
        "Position": position,
        "Auditors": auditor_email or "",
        "First audited at": reviewed_at,
    }
    return row_data


def get_theme_mapping_rows(question: Question) -> list[dict]:
    output = []
    # Get all responses with free text for this question
    # Import here to avoid circular import

    response_qs = (
        Response.objects.filter(question=question, free_text__isnull=False, free_text__gt="")
        .select_related("respondent", "annotation", "annotation__reviewed_by")
        .prefetch_related("annotation__themes", "annotation__responseannotationtheme_set__theme")
        .order_by("respondent__themefinder_id")
    )

    for response in response_qs:
        row = get_theme_mapping_output_row(response=response)
        output.append(row)
    return output


def export_user_theme(question_id: uuid.UUID, s3_key: str) -> None:
    question = Question.objects.get(id=question_id)
    output = get_theme_mapping_rows(question)
    timestamp = get_timestamp()
    question_number = question.number
    filename = f"{timestamp}_question_{question_number}_theme_changes.csv"

    if not output:
        logger.warning(f"No responses found for question {question_number}")
        return

    if settings.ENVIRONMENT == "local":
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        with open(f"downloads/{filename}", mode="w") as file:
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
    logger.info(
        f"Finishing export for question {question_number} for consultation {question.consultation.title}"
    )


@job("default", timeout=900)
def export_user_theme_job(question_id: uuid.UUID, s3_key: str) -> None:
    export_user_theme(question_id, s3_key)
