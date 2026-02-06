import csv
import datetime
import os
import uuid
from io import StringIO

import boto3
from django.conf import settings
from django_rq import job

from backend.consultations.models import (
    Question,
    Response,
)

logger = settings.LOGGER


def get_timestamp() -> str:
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d-%H%M%S")


def get_theme_mapping_output_row(
    response: Response,
) -> dict:
    # TODO: this should be a DRF serializer?
    # In new model, themes are stored as ManyToMany with through table tracking original vs current
    question = response.question
    consultation_title = question.consultation.title

    position = None

    # Get original and current themes from the annotation
    original_themes = []
    current_themes = []
    audited = False
    auditor_email = None
    reviewed_at = None

    try:
        original_themes = response.get_original_ai_themes()
        current_themes = response.get_current_themes()
        audited = response.human_reviewed
        position = response.sentiment
        if response.reviewed_by:
            auditor_email = response.reviewed_by.email
        reviewed_at = response.reviewed_at
    except Response.DoesNotExist:
        pass

    # Build theme identifiers using SelectedTheme.id
    original_theme_identifiers = [str(theme.id) for theme in original_themes]
    current_theme_identifiers = [str(theme.id) for theme in current_themes]

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
        .prefetch_related("themes", "responseannotationtheme_set__theme")
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
        logger.warning(
            "No responses found for question {question_number}", question_number=question_number
        )
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
        "Finishing export for question {question_number} for consultation {consultation_title}",
        question_number=question_number,
        consultation_title=question.consultation.title,
    )


@job("default", timeout=900)
def export_user_theme_job(question_id: uuid.UUID, s3_key: str) -> None:
    export_user_theme(question_id, s3_key)
